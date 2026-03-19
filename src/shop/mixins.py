from django.utils.deprecation import MiddlewareMixin
from django.contrib.sites.models import Site
from ipware import get_client_ip
from decimal import Decimal
import hashlib
import logging
import secrets
from django.db import transaction, DatabaseError
from django.core.cache import cache
from shop.models import Cart

logger = logging.getLogger(__name__)


class CartMiddleware(MiddlewareMixin):
    CART_TIMEOUT = 3600 * 24 * 7  # 7 дней для кэша корзины

    def process_request(self, request):
        # Инициализация сессии
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key

        # Получение текущего сайта
        try:
            current_site = Site.objects.get_current()
        except Site.DoesNotExist:
            logger.warning(f"Site not found for host: {request.get_host()}")
            return

        # Генерация безопасного browser_key
        client_ip, _ = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        browser_key = self._generate_browser_key(client_ip, user_agent)

        # Ключ для кэширования корзины
        cache_key = f"cart_{session_key}_{browser_key}_{current_site.id}"

        try:
            # Пытаемся получить корзину из кэша
            cart = cache.get(cache_key)
            if cart and self._validate_cart(cart, session_key, browser_key, current_site):
                request.cart = cart
                return

            # Если нет в кэше, обрабатываем в транзакции
            with transaction.atomic():
                cart = self._get_or_create_cart(
                    request.user, current_site, session_key, browser_key
                )

                # Кэшируем корзину
                cache.set(cache_key, cart, self.CART_TIMEOUT)

        except DatabaseError as e:
            logger.error(f"Database error in cart middleware: {e}")
            cart = self._create_fallback_cart(
                request.user, current_site, session_key, browser_key
            )
        except Exception as e:
            logger.error(f"Unexpected error in cart middleware: {e}", exc_info=True)
            cart = self._create_fallback_cart(
                request.user, current_site, session_key, browser_key
            )

        request.cart = cart

    def _generate_browser_key(self, client_ip, user_agent):
        """Генерация безопасного browser_key с salt"""
        salt = secrets.token_hex(16)
        return hashlib.sha256(f"{client_ip}:{user_agent}:{salt}".encode()).hexdigest()

    def _validate_cart(self, cart, session_key, browser_key, site):
        """Валидация корзины из кэша"""
        return (cart and cart.session_key == session_key and
                cart.browser_key == browser_key and cart.site_id == site.id)

    def _get_or_create_cart(self, user, site, session_key, browser_key):
        """Основная логика получения/создания корзины"""
        if user.is_authenticated:
            return self._handle_authenticated_user(user, site, session_key, browser_key)
        else:
            return self._handle_anonymous_user(site, session_key, browser_key)

    def _handle_authenticated_user(self, user, site, session_key, browser_key):
        """Обработка аутентифицированного пользователя"""
        # Ищем все корзины пользователя на этом сайте
        user_carts = Cart.objects.select_for_update().filter(
            user=user, site=site
        )

        # Если есть несколько корзин - объединяем их
        if user_carts.count() > 1:
            main_cart = user_carts.first()
            for extra_cart in user_carts[1:]:
                self._merge_carts(main_cart, extra_cart)
            return main_cart

        user_cart = user_carts.first()

        # Ищем временную анонимную корзину
        temp_cart = Cart.objects.filter(
            user__isnull=True, site=site, session_key=session_key
        ).first()

        if user_cart:
            if temp_cart and temp_cart.id != user_cart.id:
                self._merge_carts(user_cart, temp_cart)
            return user_cart

        # Ищем анонимную корзину по browser_key
        anonymous_cart = Cart.objects.filter(
            browser_key=browser_key, site=site, user__isnull=True
        ).first()

        if anonymous_cart:
            # Привязываем анонимную корзину к пользователю
            anonymous_cart.user = user
            anonymous_cart.session_key = session_key
            anonymous_cart.save()
            return anonymous_cart

        # Создаем новую корзину
        return Cart.objects.create(
            user=user,
            session_key=session_key,
            browser_key=browser_key,
            site=site,
            amount=Decimal("0.00"),
        )

    def _handle_anonymous_user(self, site, session_key, browser_key):
        """Обработка анонимного пользователя"""
        # Ищем корзину по session_key (приоритет)
        cart = Cart.objects.filter(
            site=site, session_key=session_key, user__isnull=True
        ).first()

        if cart:
            return cart

        # Ищем корзину по browser_key (только если та же сессия не найдена)
        existing_cart = Cart.objects.filter(
            browser_key=browser_key, site=site, user__isnull=True
        ).first()

        if existing_cart:
            # Обновляем session_key для существующей корзины
            existing_cart.session_key = session_key
            existing_cart.save()
            return existing_cart

        # Создаем новую корзину
        return Cart.objects.create(
            user=None,
            session_key=session_key,
            browser_key=browser_key,
            site=site,
            amount=Decimal("0.00"),
        )

    def _merge_carts(self, target_cart, source_cart):
        """Безопасное объединение корзин с проверкой дубликатов"""
        try:
            for sp in source_cart.selectedproduct.all():
                # Проверяем, нет ли уже такого товара в целевой корзине
                existing_item = target_cart.selectedproduct.filter(
                    product=sp.product
                ).first()

                if existing_item:
                    existing_item.quantity += sp.quantity
                    existing_item.save()
                else:
                    target_cart.selectedproduct.add(sp)

            target_cart.update_amount()
            source_cart.delete()

        except Exception as e:
            logger.error(f"Error merging carts {target_cart.id} and {source_cart.id}: {e}")
            # В случае ошибки просто удаляем source_cart
            source_cart.delete()

    def _create_fallback_cart(self, user, site, session_key, browser_key):
        """Создание резервной корзины при ошибках"""
        try:
            return Cart.objects.create(
                user=user if user.is_authenticated else None,
                session_key=session_key,
                browser_key=browser_key,
                site=site,
                amount=Decimal("0.00"),
            )
        except Exception as e:
            logger.critical(f"Failed to create fallback cart: {e}")
            # Возвращаем пустой объект чтобы не сломать запрос
            return type('EmptyCart', (), {
                'id': None,
                'selectedproduct': type('EmptyManager', (), {
                    'all': lambda: [],
                    'add': lambda x: None,
                    'filter': lambda **kwargs: type('EmptyQuerySet', (), {'first': lambda: None})()
                })()
            })()
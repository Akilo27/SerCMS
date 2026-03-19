from django import template
from django.contrib.sites.models import Site
from django.db.models import Count
from django.shortcuts import get_object_or_404

from shop.models import Categories, Valute, Cart
from shop.forms import UpdateCartCurrencyForm
from django.middleware.csrf import get_token
from ipware import get_client_ip
import hashlib
import logging
from decimal import Decimal, ROUND_DOWN
from django.contrib.contenttypes.models import ContentType
from moderation.models import ReklamBanner

register = template.Library()

logger = logging.getLogger(__name__)

@register.simple_tag
def get_user_cart_products(request):
    site = Site.objects.filter(domain=request.get_host()).first()
    if not site:
        return [], 0, 0, "Не указано", "", "0.00"

    session_key = request.session.session_key  # НЕ создаём новую сессию принудительно

    client_ip, _ = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()

    cart = None
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user, site=site).first()
    else:
        cart = Cart.objects.filter(
            browser_key=browser_key, session_key=session_key, site=site
        ).first()

    if not cart:
        return [], 0, 0, "Не указано", "", "0.00"

    selected_products = cart.selectedproduct.all()
    amount = cart.amount
    convert_valute = cart.convert_valute
    product_count = selected_products.count()
    cart_total = cart.get_formatted_total()
    valute_name = cart.valute.name if cart.valute else "Не указано"
    valute_icon = cart.valute.icon_code if cart.valute else ""
    valute_relationship = cart.valute.relationship if cart.valute and hasattr(cart.valute, "relationship") else ""
    valute_allowance = cart.valute.allowance if cart.valute and hasattr(cart.valute, "allowance") else ""
    valute_key = cart.valute.key if cart.valute else ""

    return (
        selected_products,
        amount,
        product_count,
        valute_name,
        valute_icon,
        cart_total,
        convert_valute,
        valute_relationship,
        valute_allowance,
        valute_key,
    )


@register.simple_tag(takes_context=True)
def get_categories_without_parent(context):
    request = context["request"]
    current_domain = request.get_host()
    try:
        current_site = Site.objects.get(domain=current_domain)
        return Categories.objects.filter(
            parent__isnull=True, site__in=[current_site], publishet=True
        )
    except Site.DoesNotExist:
        return Categories.objects.none()


@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key, [])
    return []


@register.simple_tag
def get_banners_for_category(category):
    """Возвращает баннеры, связанные с данной категорией"""
    content_type = ContentType.objects.get_for_model(category)
    return ReklamBanner.objects.filter(content_type=content_type, object_id=category.id)


@register.simple_tag
def get_categories_without_parent_with_products(current_domain):
    current_site = Site.objects.get(domain=current_domain)
    categories = (
        Categories.objects.filter(parent__isnull=True, site=current_site)
        .annotate(product_count=Count("products_rekomendet"))
        .order_by("create")
    )
    return categories


@register.simple_tag
def get_banners_for_category(category):
    content_type = ContentType.objects.get_for_model(Categories)
    return ReklamBanner.objects.filter(content_type=content_type, object_id=category.id)


@register.filter
def multiply(value, arg):
    return value * arg


@register.filter
def is_category_for_site(category, current_domain):
    current_site = Site.objects.get(domain=current_domain)
    if category.site.filter(id=current_site.id).exists():
        return category
    return None


@register.simple_tag
def get_child_categories_with_count(current_domain, current_category_slug=None):
    try:
        current_site = Site.objects.get(domain=current_domain)
        categories = Categories.objects.filter(
            site=current_site, publishet=True
        )  # Только опубликованные

        if current_category_slug:
            current_category = get_object_or_404(
                Categories, slug=current_category_slug, site=current_site
            )
            # Получаем дочерние категории + фильтруем те, у которых есть товары
            child_categories = current_category.children.filter(
                site=current_site, publishet=True
            ).filter(count_product__gt=0)  # Только с товарами
            return child_categories
        else:
            # Корневые категории (без родителя) + с товарами
            root_categories = (
                categories.filter(parent__isnull=True)
                .annotate(product_count=Count("products", distinct=True))
                .filter(product_count__gt=0)
            )
            return root_categories

    except Site.DoesNotExist:
        return Categories.objects.none()


@register.filter(name="pluralize")
def pluralize(value, arg):
    variants = arg.split(",")
    try:
        num = int(value)
    except (ValueError, TypeError):
        return ""

    if num % 10 == 1 and num % 100 != 11:
        return variants[0]
    elif 2 <= num % 10 <= 4 and (num % 100 < 10 or num % 100 >= 20):
        return variants[1]
    return variants[2]


@register.simple_tag
def get_categories_hierarchy(current_domain):
    current_site = Site.objects.get(domain=current_domain)
    # Получаем все опубликованные категории с подсчетом продуктов
    categories = (
        Categories.objects.filter(site=current_site, publishet=True)
        .annotate(product_count=Count("products"))
        .order_by("parent__id", "id")
    )  # Сортируем по parent для правильной иерархии

    return categories


@register.filter
def print_categories_tree(categories, parent=None):
    result = []
    for category in categories:
        if category.parent_id == parent:
            result.append(category)
            # Рекурсивно добавляем детей
            children = print_categories_tree(categories, category.id)
            if children:
                result.extend(children)
    return result


@register.filter
def multiply(value, arg):
    try:
        return int(value) * int(arg)
    except:
        return 0

@register.simple_tag(takes_context=True)
def render_update_cart_currency_form(context):
    request = context["request"]
    form = UpdateCartCurrencyForm()

    # Получаем сайт
    host = request.get_host()
    try:
        current_site = Site.objects.get(domain=host)
    except Site.DoesNotExist:
        current_site = Site.objects.get(id=1)

    # Убеждаемся, что у сессии есть ключ
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    cart = None

    if request.user.is_authenticated:
        # Ищем по user и site
        cart = Cart.objects.filter(user=request.user, site=current_site).first()
        if not cart:
            # Пробуем найти по session_key и site
            cart = Cart.objects.filter(
                session_key=session_key, site=current_site
            ).first()
    else:
        # IP и User-Agent
        client_ip, _ = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()

        cart = Cart.objects.filter(
            browser_key=browser_key, session_key=session_key, site=current_site
        ).first()

    # Корзину не создаём, если ничего не нашли
    if not cart:
        return {
            "form": form,
            "selected_valute": None,
            "csrf_token": get_token(request),
        }

    return {
        "form": form,
        "selected_valute": cart.valute,
        "csrf_token": get_token(request),
    }





@register.simple_tag
def currency_conversion(price, currency_id):
    print(f"[currency_conversion] price type: {type(price)}, value: {price}")  # Отладка
    if not isinstance(price, (int, float, Decimal)):
        return "-"

    if price and price != 0:
        try:
            currency = Valute.objects.get(id=currency_id)
        except Valute.DoesNotExist:
            return f"{int(price)}" if price == int(price) else f"{price:.2f}"

        if not currency or currency.relationship is None:
            return f"{int(price)}" if price == int(price) else f"{price:.2f}"

        relationship_value = Decimal(currency.relationship)
        price_value = Decimal(price)
        if relationship_value == 0:
                new_price = price_value
        else:
            new_price = price_value / relationship_value
        new_price = new_price.quantize(Decimal("1.00"), rounding=ROUND_DOWN)
        return f"{int(new_price)}" if new_price == int(new_price) else f"{new_price:.2f}"

    return "-"


@register.simple_tag
def currency_conversion_for_products(request, price, product_valute_id):
    print(f"[currency_conversion_for_products] Initial price: {price}, product_valute_id: {product_valute_id}")

    if not price or price == 0:
        return "-"

    if hasattr(price, "amount"):
        price = price.amount
    print(f"[currency_conversion_for_products] Normalized price: {price}")

    if not isinstance(price, (int, float, Decimal)):
        return "-"

    # Убираем знак минус, если цена отрицательная
    if price < 0:
        price = abs(price)

    user = request.user
    client_ip, _ = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()

    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    site = Site.objects.filter(domain=request.get_host()).first()
    if not site:
        print("[currency_conversion_for_products] Site not found")
        return "-"

    cart = None

    if user.is_authenticated:
        cart = Cart.objects.filter(user=user, site=site).first()
        if not cart:
            cart = Cart.objects.filter(session_key=session_key, site=site).first()
    else:
        cart = Cart.objects.filter(
            browser_key=browser_key, session_key=session_key, site=site
        ).first()

    print(f"[currency_conversion_for_products] Cart found: {cart}")

    if not cart or not cart.valute:
        print("[currency_conversion_for_products] No cart or cart.valute is None")
        return f"{int(price)}" if price == int(price) else f"{price:.2f}"

    cart_valute = cart.valute
    print(f"[currency_conversion_for_products] Cart valute: {cart_valute}")

    if not product_valute_id:
        print("[currency_conversion_for_products] No product_valute_id provided")
        return f"{int(price)}" if price == int(price) else f"{price:.2f}"

    try:
        prod_valute = Valute.objects.get(id=product_valute_id)
    except (Valute.DoesNotExist, ValueError, TypeError) as e:
        print(f"[currency_conversion_for_products] Product valute not found or invalid: {e}")
        return f"{int(price)}" if price == int(price) else f"{price:.2f}"

    print(f"[currency_conversion_for_products] Product valute: {prod_valute}")

    if (
            cart_valute.relationship is None
            or prod_valute.relationship is None
            or cart_valute.relationship == 0
    ):
        print("[currency_conversion_for_products] Invalid currency relationship values")
        return f"{int(price)}" if price == int(price) else f"{price:.2f}"

    # Всегда конвертируем из валюты продукта в валюту корзины
    try:
        conversion_rate = Decimal(prod_valute.relationship) / Decimal(cart_valute.relationship)
        print(f"[currency_conversion_for_products] Conversion rate: {conversion_rate}")
        new_price = Decimal(price) * conversion_rate

        if cart_valute.allowance and Decimal(cart_valute.allowance) != 0:
            new_price += new_price * (Decimal(cart_valute.allowance) / Decimal(100))

        new_price = new_price.quantize(Decimal("1.00"), rounding=ROUND_DOWN)
        print(f"[currency_conversion_for_products] Converted price: {new_price}")

        # Убираем знак минус, если цена отрицательная
        if new_price < 0:
            new_price = abs(new_price)

        return f"{int(new_price)}" if new_price == int(new_price) else f"{new_price:.2f}"

    except Exception as e:
        print(f"[currency_conversion_for_products] Currency conversion error: {e}")
        return f"{int(price)}" if price == int(price) else f"{price:.2f}"


@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

import decimal
import json
import math
import logging
import time
import traceback
import uuid
from datetime import datetime, timedelta
import random
from urllib3.exceptions import InsecureRequestWarning

from shop.models import Manufacturers

logger = logging.getLogger(__name__)
import requests
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.sites.models import Site
from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views import View
from django.views.generic import DetailView, TemplateView
import html

from delivery.models import DeliveryType
from payment.models import Order, PaymentType
from shop.models import Storage, StockAvailability, Cart
from django.http import HttpResponseRedirect, JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import hashlib
from _project.domainsmixin import DomainTemplateMixin
from django.core.mail import send_mail
from django.contrib import messages
from useraccount.models import Profile
from django.utils.decorators import method_decorator
from ipware import get_client_ip

import base64
import hmac
# Прокси (можно вынести в settings)
# Секретные ключи PayTR (тоже желательно через settings)




@csrf_exempt  # Если банк отправляет POST-запросы, необходимо отключить проверку CSRF
def payment_notification_alfa_bank(request):
    if request.method == "GET":
        payment_id = request.GET.get("orderNumber")
        operation = request.GET.get("operation")
        status = request.GET.get("status")
        order = Order.objects.get(key=payment_id)
        if operation == "deposited":
            if status == "1":
                order.type = 2
                order.save()
                return HttpResponse(status=200)
    return HttpResponse(status=200)



@csrf_exempt
def universal_payment_callback(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    content_type = request.content_type

    try:
        # 1. PayTR Classic (x-www-form-urlencoded)
        if content_type == "application/x-www-form-urlencoded":
            post = request.POST

            if 'hash' in post and 'callback_id' in post:
                merchant_key = "nPUAc1sf23q6D1mX"  # Удалена лишняя запятая
                merchant_salt = "NJiJb4D1REajGXRA"  # Удалена лишняя запятая

                # Формируем строку для хэширования
                hash_str = (
                    post['callback_id']
                    + post['merchant_oid']
                    + merchant_salt
                    + post['status']
                    + post['total_amount']
                )

                # Вычисляем хэш
                computed_hash = base64.b64encode(
                    hmac.new(
                        merchant_key.encode(),
                        hash_str.encode(),
                        hashlib.sha256
                    ).digest()
                ).decode()

                # Проверка хэша
                if computed_hash != post['hash']:
                    return HttpResponse("PAYTR notification failed: bad hash")

                try:
                    order = Order.objects.get(key=post['merchant_oid'])
                    if order.status == 3:
                        return HttpResponse("OK")  # уже подтверждено

                    if post['status'] == 'success':
                        order.status = 3  # оплачено
                    else:
                        order.status = 2  # отклонено

                    order.save()
                    return HttpResponse("OK")

                except Order.DoesNotExist:
                    return HttpResponse("Order not found", status=404)

            # 2. ЮMoney
            elif 'sha1_hash' in post:
                payment_data = post
                sha1_hash = payment_data.get("sha1_hash")
                notification_secret = "DBQ9CXItdptslPR3JH39MJMm"

                params_string = (
                    f"{payment_data['notification_type']}"
                    f"&{payment_data['operation_id']}"
                    f"&{payment_data['amount']}"
                    f"&{payment_data['currency']}"
                    f"&{payment_data['datetime']}"
                    f"&{payment_data['sender']}"
                    f"&{payment_data['codepro']}"
                    f"&{notification_secret}"
                    f"&{payment_data['label']}"
                )
                calculated_hash = hashlib.sha1(
                    params_string.encode("utf-8")
                ).hexdigest()

                if (
                    sha1_hash == calculated_hash
                    and payment_data.get("unaccepted") == "false"
                ):
                    key = payment_data.get("label")
                    try:
                        order = Order.objects.get(key=key)
                        order.status = 3
                        order.save()
                        return HttpResponse("OK")
                    except Order.DoesNotExist:
                        return HttpResponse("Order not found", status=404)
                else:
                    return HttpResponse("Invalid SHA1 hash", status=400)

            else:
                return HttpResponse("Unknown x-www-form-urlencoded provider", status=400)

        # 3. JSON-based уведомления
        elif content_type == "application/json":
            payment_data = json.loads(request.body)

            tracking_id = payment_data.get("transaction", {}).get("tracking_id")
            status = payment_data.get("transaction", {}).get("status")
            signature = payment_data.get("signature")

            if signature:
                secret = "YOUR_JSON_SECRET"
                expected_signature = hmac.new(
                    secret.encode(),
                    json.dumps(
                        payment_data["transaction"],
                        separators=(",", ":"),
                        sort_keys=True
                    ).encode(),
                    hashlib.sha256
                ).hexdigest()
                if signature != expected_signature:
                    return HttpResponse("Invalid signature", status=400)

            if tracking_id:
                try:
                    order = Order.objects.get(key=tracking_id)
                    order.status = 3 if status == "successful" else 2
                    order.save()
                    return HttpResponse("OK")
                except Order.DoesNotExist:
                    return HttpResponse("Order not found", status=404)
            else:
                return HttpResponse("Invalid payload", status=400)

        else:
            return HttpResponse("Unsupported Content-Type", status=415)

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return HttpResponse(
            f"Error: {str(e)}\n{tb}",
            content_type="text/plain",
            status=500
        )




@csrf_exempt
def payment_notification(request):
    notification_secret = "DBQ9CXItdptslPR3JH39MJMm"

    if request.method == "POST":
        payment_data = request.POST
        sha1_hash = payment_data.get("sha1_hash")
        if sha1_hash:
            params_string = (
                f"{payment_data['notification_type']}"
                f"&{payment_data['operation_id']}"
                f"&{payment_data['amount']}"
                f"&{payment_data['currency']}"
                f"&{payment_data['datetime']}"
                f"&{payment_data['sender']}"
                f"&{payment_data['codepro']}"
                f"&{notification_secret}"
                f"&{payment_data['label']}"
            )
            calculated_hash = hashlib.sha1(params_string.encode("utf-8")).hexdigest()
            if sha1_hash == calculated_hash:
                unaccepted = payment_data.get("unaccepted")
                if unaccepted == "false":
                    key = payment_data.get("label")
                    if key:
                        try:
                            payment = Order.objects.get(key=key)
                            payment.payment = 2
                            payment.save()
                        except Order.DoesNotExist:
                            return HttpResponse(status=404)
                    return HttpResponse(status=200)
    return HttpResponse(status=200)


@csrf_exempt
def notification_gateway(request):
    if request.method == "POST":
        try:
            payment_data = json.loads(request.body)
            tracking_id = payment_data.get("transaction", {}).get("tracking_id", "")
            status = payment_data.get("transaction", {}).get("status", "")
            if status == "successful":
                order = Order.objects.get(key=tracking_id)
                order.status = 3
                order.save()
            else:
                order = Order.objects.get(key=tracking_id)
                order.status = 1
                order.save()
            return HttpResponse(status=200)
        except Exception:
            return HttpResponse(status=500)
    else:
        return HttpResponse(status=400)

def calculate_the_shipping_cost(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        city = data.get('city')
        adress = data.get('address')
        longitude = data.get('longitude')
        latitude = data.get('latitude')
        total_weight = data.get('total_weight', 0)
        total_volume = data.get('total_volume', 0)
        items = data.get('items', [])

        # Логирование данных для отладки
        print("Полученные данные для расчета доставки:")
        print(f"Город: {city}, Адрес: {adress}")
        print(f"Координаты (longitude, latitude): {longitude}, {latitude}")
        print(f"Общий вес товаров: {total_weight} кг")
        print(f"Общий объем товаров: {total_volume} м³")
        print(f"Товары:", items)

        try:
            # Проверка значений longitude и latitude
            longitude = float(longitude) if longitude is not None else None
            latitude = float(latitude) if latitude is not None else None

            if longitude is None or latitude is None:
                raise ValueError("Недействительные координаты")

            # Данные для запроса к Яндексу
            request_data = {
                "fullname": f"{city}, {adress}",
                "start_point": [longitude, latitude],
            }

            # Получение метода доставки
            try:
                delivery_method = DeliveryType.objects.get(type=1, site__domain=request.get_host(), turn_on=True)
            except DeliveryType.DoesNotExist:
                return JsonResponse({'status': False, 'message': 'Метод доставки не найден или отключен.'})

            # URL для Яндекс Доставки
            url = "https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/delivery-methods"
            headers = {
                "Accept-Language": "ru",
                "Authorization": f"Bearer {delivery_method.key_1}",
                "Content-Type": "application/json",
            }

            response = requests.post(url, headers=headers, data=json.dumps(request_data))
            if response.status_code == 200:
                response_data = response.json()
                available_tariffs = response_data.get("express_delivery", {}).get("available_tariffs", [])
                if available_tariffs:
                    selected_tariff = min(available_tariffs, key=lambda x: x['minimal_price'])
                    price = selected_tariff['minimal_price']

                return JsonResponse({'status': True, 'message': f'{price}'})
            else:
                return JsonResponse({'status': False, 'message': "Ошибка в запросе к Яндекс Доставке"})

        except ValueError as e:
            return JsonResponse({'status': False, 'message': f"Ошибка с координатами: {str(e)}"})

def generate_paytr_token(merchant_key_bytes, hash_str_with_salt):
    """Генерация токена PayTR по HMAC SHA256 + base64"""
    return base64.b64encode(
        hmac.new(merchant_key_bytes, hash_str_with_salt.encode('utf-8'), hashlib.sha256).digest()
    ).decode('utf-8')

def json_safe(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)

PROXY = {
    'http': 'http://9Nk2C1:PpTaMN@200.10.40.102:9720',
    'https': 'http://9Nk2C1:PpTaMN@200.10.40.102:9720'
}


def generate_merchant_oid_from_uuid():
    unique_id = str(uuid.uuid4()).replace('-', '')[:30]  # Берем первые 30 символов
    return f"S{unique_id}"

class CheckoutView(DomainTemplateMixin, DetailView):
    """Cart View"""

    model = Cart
    template_name = "checkout.html"
    context_object_name = "checkout"

    def get_object(self):
        request = self.request
        user = request.user
        current_domain = request.get_host()

        if user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=user, site__domain=current_domain)
        else:
            client_ip, _ = get_client_ip(request)
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            browser_key = hashlib.md5(
                (client_ip + user_agent).encode("utf-8")
            ).hexdigest()
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            cart, _ = Cart.objects.get_or_create(
                browser_key=browser_key,
                site__domain=current_domain,
                defaults={"session_key": session_key},
            )
        return cart

    def create_paytr_link(
            self,
            merchant_id,
            merchant_key,
            merchant_salt,
            name,
            price,
            callback_link,
            callback_id,
            merchant_oid,
            link_type='product',
            currency='TL',
            max_installment='12',
            lang='tr',
            get_qr=1,
            debug_on=1,
            proxy=None,
            expiry_hours=24
    ):
        # Prepare required fields
        required = name + price + currency + max_installment + link_type + lang

        # Handle link type specific fields
        if link_type == 'product':
            min_count = '1'
            email = ''
            required += min_count
        elif link_type == 'collection':
            min_count = ''
            email = f'{random.randint(1, 9999999)}@example.com'
            required += email
        else:
            return {
                'success': False,
                'error': 'Invalid link_type. Must be "product" or "collection"'
            }

        # Prepare expiry date
        expiry_date = (datetime.now() + timedelta(hours=expiry_hours)).strftime('%Y-%m-%d %H:%M:%S')
        max_count = '1'

        # Generate token
        hash_str = required + merchant_salt
        paytr_token = base64.b64encode(
            hmac.new(merchant_key.encode('utf-8'), hash_str.encode('utf-8'), hashlib.sha256).digest()
        ).decode('utf-8')

        # Prepare request params
        params = {
            'merchant_id': merchant_id,
            'merchant_oid': merchant_oid,
            'name': name,
            'price': price,
            'currency': currency,
            'max_installment': max_installment,
            'link_type': link_type,
            'lang': lang,
            'min_count': min_count,
            'email': email,
            'expiry_date': expiry_date,
            'max_count': max_count,
            'callback_link': callback_link,
            'callback_id': callback_id,
            'debug_on': debug_on,
            'get_qr': get_qr,
            'paytr_token': paytr_token,
        }

        # Configure session
        session = requests.Session()
        if proxy:
            session.proxies = proxy
        session.verify = False

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9',
        }

        try:
            response = session.post(
                'https://www.paytr.com/odeme/api/link/create',
                data=params,
                headers=headers,
                timeout=30
            )

            # Check for access restrictions
            if "Access Restricted" in response.text:
                return {
                    'success': False,
                    'error': 'Access restricted. Check proxy or merchant credentials.',
                    'response': response.text
                }

            try:
                res = response.json()
            except json.JSONDecodeError:
                return {
                    'success': False,
                    'error': 'Invalid JSON response from server',
                    'response': response.text
                }

            if res.get('status') == 'error':
                return {
                    'success': False,
                    'error': res.get('err_msg', 'Unknown error'),
                    'response': res
                }
            elif res.get('status') == 'failed':
                return {
                    'success': False,
                    'error': res.get('reason', 'Unknown failure reason'),
                    'response': res
                }
            elif res.get('status') == 'success':
                return {
                    'success': True,
                    'link': res.get('link'),
                    'response': res
                }

            return {
                'success': False,
                'error': 'Unknown response status',
                'response': res
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}',
                'exception': e
            }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.get_object()

        # Проверка, авторизован ли пользователь
        if self.request.user.is_authenticated:
            context["adresses"] = self.request.user.get_adresses()
        else:
            # Можно добавить сообщение или оставить пустым
            context["adresses"] = []
            # Или, например, добавить сообщение:
            # context["auth_message"] = "Пожалуйста, авторизуйтесь, чтобы видеть адреса."

        selected_products = cart.selectedproduct.all()
        context["selected_products"] = selected_products
        context["gabarite"] = selected_products

        context["product_data"] = [
            {
                'product': selected_product.product,
                'weight': selected_product.product.weight,
                'width': selected_product.product.width,
                'height': selected_product.product.height,
                'length': selected_product.product.length,
                'quantity': selected_product.quantity,
            }
            for selected_product in selected_products
        ]
        context["enabled_payment_types"] = PaymentType.objects.filter(turn_on=True)
        context["manufacturers"] = Manufacturers.objects.all()
        context["valute"] = cart.valute
        context["deliverytype"] = DeliveryType.objects.filter(
            site__domain=self.request.get_host(), turn_on=True
        )
        context["storage"] = Storage.objects.first()

        return context

    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        BEGATEWAY_API_URL = "https://gateway.akari-upm.com"

        data = request.POST
        customer_name = data.get("customer_name")
        customer_surname = data.get("customer_surname")
        customer_phone = data.get("customer_phone")
        customer_email = data.get("customer_email")
        purchase_type = data.get("payment_type")
        delivery_price = data.get("delivery-price")
        address = data.get("address")
        city = data.get("city")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        sflat = data.get("sflat")
        sfloor = data.get("sfloor")
        porch = data.get("porch")
        user_comment = data.get("user_comment")
        selected_pvz = request.POST.get('selected_pvz')
        delivery_price_str = request.POST.get('delivery_price', '').strip()
        try:
            delivery_price = decimal.Decimal(delivery_price_str)
        except (decimal.InvalidOperation, ValueError):
            delivery_price = decimal.Decimal('0')


        current_domain = request.get_host()
        current_site = Site.objects.get(domain=current_domain)

        # Получение корзины и создание пользователя при необходимости
        if request.user.is_authenticated:
            user = request.user
            cart = Cart.objects.get(user=user, site=current_site)
        else:
            password = get_random_string(length=8)
            try:
                temp_cart = self.get_object()
                user = Profile.objects.create_user(
                    username=customer_email,
                    email=customer_email,
                    password=password,
                    first_name=customer_name,
                    last_name=customer_surname,
                )
                cart = Cart.objects.create(
                    amount=temp_cart.amount, site=current_site, user=user
                )
                cart.selectedproduct.set(temp_cart.selectedproduct.all())
                cart.save()

                login_user = authenticate(
                    request, username=customer_email, password=password
                )
                if login_user:
                    login(request, login_user)

                send_mail(
                    "Ваш аккаунт был создан",
                    f"Здравствуйте, {customer_name}!\n\nВаш аккаунт был успешно создан.\n"
                    f"Ваше имя пользователя: {customer_email}\nВаш пароль: {password}\n\n"
                    f"Пожалуйста, смените пароль после первого входа.",
                    "info@4-market.ru",
                    [customer_email],
                    fail_silently=False,
                )
            except IntegrityError:
                messages.error(
                    request,
                    "Пользователь с такой почтой уже существует. Войдите в аккаунт.",
                )
                return redirect(reverse("webmain:login"))

        # Создание заказа
        order_data = {
            "user": user,
            "phone_number": customer_phone,
            "customer_name": customer_name,
            "customer_surname": customer_surname,
            "customer_email": customer_email,
            "site": current_site,
        }

        if delivery_price and delivery_price != "0":
            order_data.update(
                {
                    "all_amount": cart.amount + math.ceil(float(delivery_price)),
                    "delivery_price": math.ceil(float(delivery_price)),
                    "requires_delivery": True,
                    "longitude": longitude,
                    "latitude": latitude,
                    "city": city,
                    "adress": address,
                    "sflat": sflat,
                    "sfloor": sfloor,
                    "porch": porch,
                    "user_comment": user_comment,
                }
            )
        else:
            order_data["all_amount"] = cart.amount

        order = Order.objects.create(**order_data)
        order.selectedproduct.set(cart.selectedproduct.all())
        order.mail_send = True
        print(request.POST)
        if delivery_price > 0:
            order.delivery_address = selected_pvz
            order.requires_delivery = True
            order.total_amount = decimal.Decimal(order.amount)
            order.delivery_price = delivery_price
            order.total_amount += delivery_price
        order.save()

        # Очистка корзины
        cart.selectedproduct.clear()
        cart.amount = 0
        cart.save()

        payment_amount = order.all_amount
        payment_description = order.key

        if payment_amount == 0:
            return HttpResponse("Ошибка оплаты: сумма 0")

        # Yoomoney
        if purchase_type == "1":
            pt = PaymentType.objects.filter(type=1, turn_on=True).first()
            redirect_url = (
                f"https://yoomoney.ru/quickpay/confirm.xml?receiver={pt.shop_key}"
                f"&formcomment={payment_description}&short-dest={payment_description}"
                f"&quickpay-form=shop&targets={payment_description}"
                f"&sum={payment_amount}&label={payment_description}"
            )
            order.purchase_url = redirect_url
            order.save()
            return HttpResponseRedirect(redirect_url)

        # Alfa-Bank
        if purchase_type == '4':
            pt = PaymentType.objects.filter(type=int(purchase_type), turn_on=True).first()

            alfa_request_data = {
                'token': f'{pt.key_1}',
                'orderNumber': order.key,
                'amount': int(payment_amount * 100),
                'returnUrl': f"https://{current_domain}/myorder",
                'failUrl': f"https://{current_domain}/myorder"
            }

            response = requests.post('https://payment.alfabank.ru/payment/rest/register.do', data=alfa_request_data)

            if response.status_code == 200:
                try:
                    response_data = response.json()
                    redirect_url = response_data.get('formUrl')

                    if redirect_url:
                        order.purchase_url = redirect_url
                        order.save()
                        return HttpResponseRedirect(redirect_url)
                    else:
                        return HttpResponse(f"Ошибка платежа: formUrl не найден. Ответ: {response_data}")

                except requests.exceptions.JSONDecodeError:
                    return HttpResponse(f"Ошибка декодирования ответа JSON. Ответ сервера: {response.text}")

            else:
                return HttpResponse(
                    f"Ошибка платежа Альфа-Банка. Статус: {response.status_code}. Ответ: {response.text}")

        # Begateway
        if purchase_type == "3":
            pt = PaymentType.objects.filter(type=3, turn_on=True).first()
            headers = {"Authorization": f"Bearer {pt.key_1}"}
            payment_data = {
                "order_id": order.id,
                "amount": payment_amount,
                "currency": "RUB",
                "description": f"Оплата заказа #{order.id}",
                "payment_method": "bankcard",
                "payment_method_type": "bankcard",
                "email": customer_email,
                "phone": customer_phone,
            }

            try:
                response = requests.post(
                    BEGATEWAY_API_URL, json=payment_data, headers=headers
                )
                if response.status_code == 200:
                    redirect_url = response.json().get("payment_url")
                    if redirect_url:
                        order.purchase_url = redirect_url
                        order.save()
                        return HttpResponseRedirect(redirect_url)
                    return HttpResponse("Ошибка: платежный URL не получен.")
                return HttpResponse("Ошибка запроса в Begateway.")
            except requests.exceptions.RequestException as e:
                return HttpResponse(f"Ошибка запроса: {e}")

        # PayTR
        if purchase_type == "10":
            pt = PaymentType.objects.filter(type=10, turn_on=True).first()
            if not pt:
                return HttpResponse("PayTR payment method not configured")
            order_key = generate_merchant_oid_from_uuid()

            try:
                # Проверяем, что сумма платежа целочисленная
                try:
                    payment_amount_int = int(float(payment_amount))
                except (ValueError, TypeError):
                    return HttpResponse("Invalid payment amount format")

                result = self.create_paytr_link(
                    merchant_id="592296",
                    merchant_key="nPUAc1sf23q6D1mX",
                    merchant_salt="NJiJb4D1REajGXRA",
                    name=f"Order #{order.id}",
                    price=str(payment_amount_int),
                    callback_link=f"https://{current_domain}/en/payments/callback/",
                    callback_id=str(order.id),
                    merchant_oid=order_key,
                    link_type="product",
                    currency="TL",
                    max_installment="12",
                    lang="tr",
                    get_qr=0,
                    debug_on=1,
                    proxy=PROXY
                )

                if not result['success']:
                    error_msg = result.get('error', 'No error details')
                    response_data = result.get('response', 'No response')
                    return HttpResponse(
                        f"PayTR error: {error_msg}<br>Response: {response_data}"
                    )

                order.purchase_url = result['link']
                order.save()
                return HttpResponseRedirect(result['link'])

            except Exception as e:
                return HttpResponse(f"PayTR processing failed: {str(e)}")

        return redirect(reverse("shop:my_order"))


#
# class CreateOrderView(View):
#     @method_decorator(
#         csrf_exempt
#     )  # Отключаем CSRF для POST-запросов (используйте с осторожностью)
#     def post(self, request, *args, **kwargs):
#         BEGATEWAY_API_URL = "https://gateway.akari-upm.com"
#
#         # Получаем данные из POST-запроса
#         customer_name = request.POST.get("customer_name")
#         customer_surname = request.POST.get("customer_surname")
#         customer_phone = request.POST.get("customer_phone")
#         customer_email = request.POST.get("customer_email")
#         purchase_type = request.POST.get("payment_type")
#         delivery_price = request.POST.get("delivery-price")
#         address = request.POST.get("address")
#         city = request.POST.get("city")
#         latitude = request.POST.get("latitude")
#         longitude = request.POST.get("longitude")
#         sflat = request.POST.get("sflat")
#         sfloor = request.POST.get("sfloor")
#         porch = request.POST.get("porch")
#         user_comment = request.POST.get("user_comment")
#
#         # Если пользователь авторизован — берем корзину по пользователю и текущему сайту
#         if request.user.is_authenticated:
#             user = request.user
#             cart = Cart.objects.get(user=user, site__domain=request.get_host())
#         else:
#             # Если не авторизован — создаем пользователя с рандомным паролем
#             password = get_random_string(length=8)
#             try:
#                 cartnotauth = (
#                     self.get_object()
#                 )  # Ваш метод для получения корзины неавторизованного
#                 user = Profile.objects.create_user(
#                     username=customer_email,
#                     email=customer_email,
#                     password=password,
#                     first_name=customer_name,
#                     last_name=customer_surname,
#                 )
#                 # Получаем текущий сайт
#                 site = Site.objects.get(domain=request.get_host())
#                 # Копируем выбранные товары из анонимной корзины в новую корзину с пользователем
#                 selectedproduct = cartnotauth.selectedproduct.all()
#                 cart = Cart.objects.create(
#                     amount=cartnotauth.amount, site=site, user=user
#                 )
#                 cart.selectedproduct.set(selectedproduct)
#                 cart.save()
#
#                 # Проводим аутентификацию и логиним пользователя
#                 auth_user = authenticate(
#                     request, username=customer_email, password=password
#                 )
#                 if auth_user:
#                     login(request, auth_user)
#                     # Отправляем письмо с данными аккаунта
#                     send_mail(
#                         "Ваш аккаунт был создан",
#                         f"Здравствуйте, {customer_name}!\n\nВаш аккаунт был успешно создан.\n"
#                         f"Ваше имя пользователя: {customer_email}\nВаш пароль: {password}\n\n"
#                         f"Пожалуйста, смените пароль после первого входа.",
#                         "info@4-market.ru",
#                         [customer_email],
#                         fail_silently=False,
#                     )
#             except IntegrityError:
#                 # Если пользователь с такой почтой уже существует — показываем сообщение и редиректим на логин
#                 messages.success(
#                     request,
#                     "Пользователь с такой почтой уже существует. Убедитесь, что почта введена правильно и войдите в свой аккаунт.",
#                 )
#                 return redirect(reverse("useraccount:login"))
#
#         # Получаем текущий домен и объект сайта
#         current_domain = request.get_host()
#         current_site = Site.objects.get(domain=current_domain)
#
#         # Проверяем, нужна ли доставка
#         delivery = delivery_price and delivery_price != "0"
#         # Считаем итоговую сумму с учетом доставки
#         total_amount = cart.amount + (
#             math.ceil(float(delivery_price)) if delivery else 0
#         )
#
#         # Создаем объект заказа с данными из формы и корзины
#         order = Order.objects.create(
#             user=user,
#             phone_number=customer_phone,
#             customer_name=customer_name,
#             customer_surname=customer_surname,
#             customer_email=customer_email,
#             all_amount=total_amount,
#             delivery_price=math.ceil(float(delivery_price)) if delivery else 0,
#             longitude=longitude,
#             latitude=latitude,
#             city=city,
#             adress=address,
#             sflat=sflat,
#             sfloor=sfloor,
#             porch=porch,
#             user_comment=user_comment,
#             requires_delivery=delivery,
#             site=current_site,
#         )
#
#         # Добавляем выбранные товары в заказ
#         selected_products = cart.selectedproduct.all()
#         order.selectedproduct.add(*selected_products)
#
#         order.mail_send = True  # Отмечаем, что письмо должно быть отправлено (если у вас есть логика на это)
#         order.save()
#
#         # Очищаем корзину пользователя после создания заказа
#         cart.selectedproduct.clear()
#         cart.amount = 0
#         cart.save()
#
#         payment_amount = order.all_amount
#         payment_description = (
#             order.key
#         )  # предполагается, что это уникальный идентификатор заказа
#
#         # Проверяем сумму — если 0, возвращаем ошибку
#         if payment_amount == 0:
#             return HttpResponse("Ошибка: сумма оплаты равна нулю.")
#
#         # Обработка оплаты в зависимости от типа платежа
#
#         # 1. YooMoney
#         if purchase_type == "1":
#             pt = PaymentType.objects.filter(type=1, turn_on=True).first()
#             redirect_url = (
#                 f"https://yoomoney.ru/quickpay/confirm.xml?"
#                 f"receiver={pt.shop_key}&formcomment={payment_description}&short-dest={payment_description}"
#                 f"&quickpay-form=shop&targets={payment_description}&sum={payment_amount}&label={payment_description}"
#             )
#             order.purchase_url = redirect_url
#             order.save()
#             return HttpResponseRedirect(redirect_url)
#
#         # 2. Альфа-Банк
#         elif purchase_type == "4":
#             pt = PaymentType.objects.filter(type=4, turn_on=True).first()
#             data = {
#                 "token": pt.key_1,
#                 "orderNumber": order.key,
#                 "amount": int(payment_amount * 100),  # сумма в копейках
#                 "returnUrl": f"https://{current_domain}/myorder",
#                 "failUrl": f"https://{current_domain}/myorder",
#             }
#             response = requests.post(
#                 "https://payment.alfabank.ru/payment/rest/register.do", data=data
#             )
#             if response.status_code == 200:
#                 response_data = response.json()
#                 redirect_url = response_data.get("formUrl")
#                 if redirect_url:
#                     order.purchase_url = redirect_url
#                     order.save()
#                     return HttpResponseRedirect(redirect_url)
#                 return HttpResponse(
#                     f"Ошибка: formUrl не найден. Ответ: {response_data}"
#                 )
#             return HttpResponse(
#                 f"Ошибка Альфа-Банка: {response.status_code} — {response.text}"
#             )
#
#         # 3. Begateway
#         elif purchase_type == "3":
#             pt = PaymentType.objects.filter(type=3, turn_on=True).first()
#             payment_data = {
#                 "order_id": order.id,
#                 "amount": payment_amount,
#                 "currency": "RUB",
#                 "description": f"Payment for Order #{order.id}",
#                 "payment_method": "bankcard",
#                 "first_name": customer_name,
#                 "last_name": customer_surname,
#                 "region": "",
#                 "adress": address,
#                 "city": city,
#                 "state": "",
#                 "zip_index": "",
#                 "phone": customer_phone,
#                 "email": customer_email,
#             }
#             headers = {"Authorization": f"Bearer {pt.key_1}"}
#             try:
#                 response = requests.post(
#                     BEGATEWAY_API_URL, json=payment_data, headers=headers
#                 )
#                 if response.status_code == 200:
#                     redirect_url = response.json().get("payment_url")
#                     if redirect_url:
#                         order.purchase_url = redirect_url
#                         order.save()
#                         return HttpResponseRedirect(redirect_url)
#                     return HttpResponse("Ошибка: не удалось получить ссылку на оплату.")
#                 return HttpResponse("Ошибка запроса в Begateway.")
#             except requests.exceptions.RequestException as e:
#                 return HttpResponse(f"Ошибка: {str(e)}")
#
#         elif purchase_type == "10":
#             pt = PaymentType.objects.filter(type=5, turn_on=True).first()
#             if not pt:
#                 return HttpResponse("Платёжная система PayTR не активна.")
#
#             merchant_id = pt.key_1
#             merchant_key = pt.key_2
#             merchant_salt = pt.key_3
#
#             user_ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
#             email = customer_email
#             payment_amount_kurus = int(payment_amount * 100)
#             merchant_oid = str(order.key)
#             success_url = f"https://{current_domain}/myorder"
#             fail_url = f"https://{current_domain}/myorder"
#             user_basket = f"Оплата заказа #{order.key}"
#
#             data_to_hash = f"{merchant_id}{user_ip}{merchant_oid}{email}{payment_amount_kurus}{success_url}{fail_url}{user_basket}{merchant_salt}"
#             paytr_token = base64.b64encode(
#                 hmac.new(
#                     merchant_key.encode("utf-8"),
#                     data_to_hash.encode("utf-8"),
#                     hashlib.sha256,
#                 ).digest()
#             ).decode()
#
#             post_data = {
#                 "merchant_id": merchant_id,
#                 "user_ip": user_ip,
#                 "merchant_oid": merchant_oid,
#                 "email": email,
#                 "payment_amount": payment_amount_kurus,
#                 "paytr_token": paytr_token,
#                 "user_basket": json.dumps([[user_basket, f"{payment_amount}", 1]]),
#                 "no_installment": 0,
#                 "max_installment": 12,
#                 "currency": "TL",
#                 "test_mode": "1" if settings.DEBUG else "0",
#                 "merchant_ok_url": success_url,
#                 "merchant_fail_url": fail_url,
#                 "timeout_limit": "30",
#                 "debug_on": "1",
#                 "language": "tr",
#             }
#
#             try:
#                 response = requests.post(
#                     "https://www.paytr.com/odeme/api/get-token", data=post_data
#                 )
#                 result = response.json()
#                 if result.get("status") == "success":
#                     token = result["token"]
#                     redirect_url = f"https://www.paytr.com/odeme/guvenli/{token}"
#                     order.purchase_url = redirect_url
#                     order.save()
#                     return HttpResponseRedirect(redirect_url)
#                 else:
#                     return HttpResponse(
#                         "Ошибка PayTR: " + result.get("reason", "Неизвестная ошибка")
#                     )
#             except Exception as e:
#                 return HttpResponse("Ошибка PayTR: " + str(e))
#
#         # По умолчанию редиректим пользователя на страницу заказов
#         return redirect(reverse("shop:my_order"))


class CustomCheckoutUrl(DomainTemplateMixin, TemplateView):
    # Этот класс отвечает за отображение и обработку страницы оплаты заказа.
    # Наследуется от TemplateView — то есть показывает HTML-шаблон и умеет обрабатывать GET и POST запросы.
    # Также наследуется DomainTemplateMixin — видимо, для работы с мультидоменностью или шаблонами по домену.

    template_name = "purchase"  # Имя шаблона для отображения страницы (purchase.html или purchase с расширением)

    def get_context_data(self, **kwargs):
        # Метод для передачи данных в шаблон при GET-запросе (загрузка страницы)
        context = super().get_context_data(**kwargs)

        # Получаем объект заказа по ключу из URL (например, ключ передан в URL)
        order = Order.objects.get(
            key=kwargs.get("key")
        )  # order - конкретный заказ пользователя

        # Получаем все товары, которые пользователь выбрал в этом заказе
        selected_products = order.selectedproduct.all()

        # Передаём в шаблон заказ и выбранные товары
        context["order"] = order
        context["selected_products"] = selected_products

        # Получаем все активные способы оплаты, чтобы показать их на странице
        enabled_payment_types = PaymentType.objects.filter(turn_on=True)
        context["enabled_payment_types"] = enabled_payment_types

        # Получаем первый объект Storage (видимо, хранение данных или настроек)
        context["storage"] = Storage.objects.first()

        return context

    def post(self, request, *args, **kwargs):
        # Обработка POST-запроса — пользователь выбрал способ оплаты и отправил форму

        BEGATEWAY_API_URL = (
            "https://gateway.akari-upm.com"  # API для платежного шлюза Begateway
        )

        # Получаем заказ по ключу из URL
        order = Order.objects.get(key=kwargs.get("key"))

        # Получаем выбранный пользователем тип оплаты из POST-данных
        purchase_type = request.POST.get("payment_type")

        # Текущий домен сайта, нужен для формирования ссылок возврата после оплаты
        current_domain = self.request.get_host()

        # Сумма к оплате и описание платежа (используем ключ заказа)
        payment_amount = order.all_amount
        payment_description = order.key

        # Проверяем, что сумма оплаты не равна 0 — иначе платеж бессмысленен
        if payment_amount == 0:
            return HttpResponse("Error payment: " + str(payment_amount))

        # Если выбран тип оплаты 1 (YooMoney)
        if purchase_type == "1":
            pt = PaymentType.objects.filter(
                type=int(purchase_type), turn_on=True
            ).first()
            # Формируем URL для быстрой оплаты YooMoney с нужными параметрами
            redirect_url = (
                f"https://yoomoney.ru/quickpay/confirm.xml?"
                f"receiver={pt.shop_key}&formcomment={payment_description}&short-dest={payment_description}"
                f"&quickpay-form=shop&targets={payment_description}&sum={payment_amount}&label={payment_description}"
            )
            # Сохраняем URL оплаты в заказе и перенаправляем пользователя
            order.purchase_url = redirect_url
            order.save()
            return HttpResponseRedirect(redirect_url)

        # Если выбран тип оплаты 4 (Альфа-Банк)
        if purchase_type == "4":
            pt = PaymentType.objects.filter(
                type=int(purchase_type), turn_on=True
            ).first()

            # Подготавливаем данные для запроса регистрации платежа в Альфа-Банке
            alfa_request_data = {
                "token": f"{pt.key_1}",
                "orderNumber": order.key,
                "amount": payment_amount * 100,  # в копейках
                "returnUrl": f"https://{current_domain}/myorder",
                "failUrl": f"https://{current_domain}/myorder",
            }

            # Отправляем POST-запрос в API Альфа-Банка
            response = requests.post(
                "https://payment.alfabank.ru/payment/rest/register.do",
                data=alfa_request_data,
            )

            # Если ответ успешный
            if response.status_code == 200:
                try:
                    # Парсим JSON с данными ответа
                    response_data = response.json()
                    redirect_url = response_data.get("formUrl")

                    # Если получили URL формы оплаты — перенаправляем пользователя
                    if redirect_url:
                        order.purchase_url = redirect_url
                        order.save()
                        return HttpResponseRedirect(redirect_url)
                    else:
                        # Если URL не найден — показываем ошибку
                        return HttpResponse(
                            f"Ошибка платежа: formUrl не найден. Ответ: {response_data}"
                        )

                except requests.exceptions.JSONDecodeError:
                    # Ошибка при разборе JSON — показываем ответ сервера для отладки
                    return HttpResponse(
                        f"Ошибка декодирования ответа JSON. Ответ сервера: {response.text}"
                    )

            else:
                # Ошибка на стороне Альфа-Банка — показываем статус и ответ
                return HttpResponse(
                    f"Ошибка платежа Альфа-Банка. Статус: {response.status_code}. Ответ: {response.text}"
                )

        # Если выбран тип оплаты 3 (Begateway)
        elif purchase_type == "3":
            pt = PaymentType.objects.filter(
                type=int(purchase_type), turn_on=True
            ).first()

            # Формируем данные платежа для API Begateway
            payment_data = {
                "order_id": order.id,
                "amount": payment_amount,
                "currency": "RUB",  # Валюта платежа
                "description": "Payment for Order #" + str(order.id),
                "payment_method": "bankcard",
                "payment_method_type": "bankcard",
                "first_name": "first_name",  # Тут можно подставить реальные данные покупателя
                "last_name": "last_name",
                "region": "region",
                "adress": "adress",
                "city": "city",
                "state": "state",
                "zip_index": "zip_index",
                "phone": "phone",
                "email": "email",
            }
            headers = {"Authorization": f"Bearer {pt.key_1}"}
            try:
                # Отправляем запрос на создание платежа в Begateway
                response = requests.post(
                    BEGATEWAY_API_URL, json=payment_data, headers=headers
                )
                if response.status_code == 200:
                    redirect_url = response.json().get("payment_url")
                    print("redirect_url----------", redirect_url)
                    if redirect_url:
                        order.purchase_url = redirect_url
                        order.save()
                        return HttpResponseRedirect(redirect_url)
                    else:
                        return HttpResponse(
                            "Payment URL not available. Please contact support."
                        )
                else:
                    return HttpResponse("Payment request to Begateway failed.")
            except requests.exceptions.RequestException as e:
                # При ошибке соединения возвращаем текст ошибки
                return HttpResponse("Error: " + str(e))

        # Если выбран тип оплаты 5 (PayTR)
        elif purchase_type == "10":
            pt = PaymentType.objects.filter(type=5, turn_on=True).first()

            if not pt:
                return HttpResponse("PayTR недоступен.")

            merchant_id = pt.shop_key
            merchant_key = pt.key_1
            merchant_salt = pt.key_2

            user_ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
            email = order.customer_email or "noemail@example.com"
            payment_amount_kurus = int(
                order.all_amount * 100
            )  # PayTR требует сумму в kuruş (1 TRY = 100 kuruş)
            merchant_oid = order.key  # уникальный номер заказа

            # URL возврата и оповещения
            return_url = f"https://{current_domain}/myorder"
            fail_url = f"https://{current_domain}/myorder"
            notify_url = f"https://{current_domain}/paytr/callback/"

            # Хеш по формуле PayTR
            hash_str = f"{merchant_id}{user_ip}{merchant_oid}{email}{payment_amount_kurus}{return_url}{merchant_salt}"
            paytr_token = base64.b64encode(
                hmac.new(
                    merchant_key.encode("utf-8"),
                    hash_str.encode("utf-8"),
                    hashlib.sha256,
                ).digest()
            ).decode("utf-8")

            paytr_data = {
                "merchant_id": merchant_id,
                "user_ip": user_ip,
                "callback_id": merchant_oid,
                "email": email,
                "payment_amount": payment_amount_kurus,
                "paytr_token": paytr_token,
                "user_name": f"{order.customer_name} {order.customer_surname}",
                "user_address": order.adress or "No Address",
                "user_phone": order.phone_number or "0000000000",
                "merchant_ok_url": return_url,
                "merchant_fail_url": fail_url,
                "timeout_limit": "30",
                "currency": "TL",  # или "RUB" если поддерживается, уточните у PayTR
                "test_mode": "1",
                "no_installment": "0",
                "lang": "en",
                "debug_on": "1",
                "merchant_notify_url": notify_url,
            }

            try:
                response = requests.post(
                    "https://www.paytr.com/odeme/api/get-token", data=paytr_data
                )
                response_data = response.json()

                if response_data.get("status") == "success":
                    token = response_data.get("token")
                    iframe_url = f"https://www.paytr.com/odeme/guvenli/{token}"
                    order.purchase_url = iframe_url
                    order.save()
                    return HttpResponseRedirect(iframe_url)
                else:
                    return HttpResponse(f"PayTR Error: {response_data.get('reason')}")
            except Exception as e:
                return HttpResponse(f"PayTR Exception: {str(e)}")

        # Если тип оплаты не распознан — перенаправляем пользователя в личный кабинет заказов
        return redirect(reverse("shop:my_order"))

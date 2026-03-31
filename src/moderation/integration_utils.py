# moderation/integration_utils.py
import requests
import json
from django.conf import settings
from django.utils import timezone
from .models import IntegrationService, IntegrationLog


class IntegrationClient:
    """Базовый клиент для работы с интеграциями"""

    def __init__(self, integration):
        self.integration = integration
        self.base_url = integration.api_url
        self.api_key = integration.api_key
        self.api_secret = integration.api_secret

    def _make_request(self, method, endpoint, data=None, headers=None):
        """Выполнить запрос к API"""
        start_time = timezone.now()
        url = f"{self.base_url}{endpoint}"

        default_headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        if headers:
            default_headers.update(headers)

        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                headers=default_headers,
                timeout=30
            )

            duration = (timezone.now() - start_time).total_seconds()

            # Логируем запрос
            IntegrationLog.objects.create(
                integration=self.integration,
                operation='webhook',
                status='success' if response.status_code < 400 else 'error',
                request_data={'method': method, 'endpoint': endpoint, 'data': data},
                response_data={'status_code': response.status_code, 'data': response.json() if response.text else {}},
                duration=duration,
                completed_at=timezone.now()
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            duration = (timezone.now() - start_time).total_seconds()

            IntegrationLog.objects.create(
                integration=self.integration,
                operation='webhook',
                status='error',
                request_data={'method': method, 'endpoint': endpoint, 'data': data},
                error_message=str(e),
                duration=duration,
                completed_at=timezone.now()
            )
            raise

    def get(self, endpoint, params=None):
        """GET запрос"""
        return self._make_request('GET', endpoint, data=params)

    def post(self, endpoint, data=None):
        """POST запрос"""
        return self._make_request('POST', endpoint, data=data)

    def put(self, endpoint, data=None):
        """PUT запрос"""
        return self._make_request('PUT', endpoint, data=data)

    def delete(self, endpoint):
        """DELETE запрос"""
        return self._make_request('DELETE', endpoint)


class MarketplaceClient(IntegrationClient):
    """Клиент для работы с маркетплейсами"""

    def get_products(self, page=1, per_page=100):
        """Получить список товаров"""
        return self.get('/products', params={'page': page, 'per_page': per_page})

    def update_product_price(self, product_id, price):
        """Обновить цену товара"""
        return self.put(f'/products/{product_id}', data={'price': price})

    def update_product_stock(self, product_id, stock):
        """Обновить остаток товара"""
        return self.put(f'/products/{product_id}', data={'stock': stock})

    def get_orders(self, date_from=None, date_to=None):
        """Получить список заказов"""
        params = {}
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        return self.get('/orders', params=params)

    def update_order_status(self, order_id, status):
        """Обновить статус заказа"""
        return self.put(f'/orders/{order_id}', data={'status': status})


class PaymentClient(IntegrationClient):
    """Клиент для работы с платежными системами"""

    def create_payment(self, amount, currency='RUB', description=None):
        """Создать платеж"""
        data = {
            'amount': amount,
            'currency': currency,
            'description': description
        }
        return self.post('/payments', data=data)

    def get_payment_status(self, payment_id):
        """Получить статус платежа"""
        return self.get(f'/payments/{payment_id}')

    def refund_payment(self, payment_id, amount=None):
        """Вернуть платеж"""
        data = {}
        if amount:
            data['amount'] = amount
        return self.post(f'/payments/{payment_id}/refund', data=data)


class DeliveryClient(IntegrationClient):
    """Клиент для работы со службами доставки"""

    def create_order(self, order_data):
        """Создать заказ на доставку"""
        return self.post('/orders', data=order_data)

    def get_order_status(self, order_id):
        """Получить статус заказа"""
        return self.get(f'/orders/{order_id}/status')

    def get_tracking_info(self, tracking_number):
        """Получить информацию по трек-номеру"""
        return self.get(f'/tracking/{tracking_number}')

    def print_label(self, order_id):
        """Получить этикетку для печати"""
        return self.get(f'/orders/{order_id}/label')


class MessengerClient(IntegrationClient):
    """Клиент для работы с мессенджерами"""

    def send_message(self, chat_id, text, attachments=None):
        """Отправить сообщение"""
        data = {
            'chat_id': chat_id,
            'text': text,
            'attachments': attachments or []
        }
        return self.post('/messages', data=data)

    def get_updates(self, offset=None):
        """Получить обновления"""
        params = {}
        if offset:
            params['offset'] = offset
        return self.get('/updates', params=params)

    def set_webhook(self, webhook_url):
        """Установить webhook"""
        return self.post('/webhook', data={'url': webhook_url})


def get_integration_client(integration_id):
    """Получить клиент для интеграции"""
    integration = IntegrationService.objects.get(id=integration_id, is_active=True)

    if integration.service_type == 'marketplace':
        return MarketplaceClient(integration)
    elif integration.service_type == 'payment':
        return PaymentClient(integration)
    elif integration.service_type == 'delivery':
        return DeliveryClient(integration)
    elif integration.service_type == 'messenger':
        return MessengerClient(integration)
    else:
        return IntegrationClient(integration)
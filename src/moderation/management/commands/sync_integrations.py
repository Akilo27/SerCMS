# moderation/management/commands/sync_integrations.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from moderation.models import IntegrationService, IntegrationLog
from moderation.integration_utils import get_integration_client

from moderation.models import MessengerMessage, DeliveryOrder, MarketplaceProduct, MarketplaceOrder


class Command(BaseCommand):
    help = 'Синхронизация данных с внешними сервисами'

    def add_arguments(self, parser):
        parser.add_argument('--type', type=str, help='Тип интеграции (marketplace/payment/delivery/messenger)')
        parser.add_argument('--integration', type=int, help='ID конкретной интеграции')

    def handle(self, *args, **options):
        integrations = IntegrationService.objects.filter(is_active=True)

        if options.get('type'):
            integrations = integrations.filter(service_type=options['type'])

        if options.get('integration'):
            integrations = integrations.filter(id=options['integration'])

        for integration in integrations:
            self.stdout.write(f"Синхронизация {integration.name}...")

            try:
                client = get_integration_client(integration.id)

                if integration.service_type == 'marketplace':
                    self.sync_marketplace(integration, client)
                elif integration.service_type == 'delivery':
                    self.sync_delivery(integration, client)
                elif integration.service_type == 'messenger':
                    self.sync_messenger(integration, client)

                integration.last_sync = timezone.now()
                integration.sync_status = 'success'
                integration.save()

                self.stdout.write(self.style.SUCCESS(f"  Успешно: {integration.name}"))

            except Exception as e:
                integration.sync_status = 'error'
                integration.error_message = str(e)
                integration.save()

                IntegrationLog.objects.create(
                    integration=integration,
                    operation='error',
                    status='error',
                    error_message=str(e),
                    completed_at=timezone.now()
                )

                self.stdout.write(self.style.ERROR(f"  Ошибка: {integration.name} - {str(e)}"))

    def sync_marketplace(self, integration, client):
        """Синхронизация маркетплейса"""
        try:
            # Получаем товары
            products = client.get_products()
            self.stdout.write(f"    Получено товаров: {len(products)}")

            # Обновляем в БД
            for product_data in products:
                MarketplaceProduct.objects.update_or_create(
                    marketplace=integration,
                    marketplace_product_id=product_data['id'],
                    defaults={
                        'marketplace_sku': product_data.get('sku', ''),
                        'price': product_data.get('price', 0),
                        'stock': product_data.get('stock', 0),
                        'status': product_data.get('status', 'active'),
                        'last_sync': timezone.now()
                    }
                )

            # Получаем заказы
            orders = client.get_orders()
            self.stdout.write(f"    Получено заказов: {len(orders)}")

            for order_data in orders:
                MarketplaceOrder.objects.update_or_create(
                    marketplace=integration,
                    marketplace_order_id=order_data['id'],
                    defaults={
                        'order_date': order_data.get('date'),
                        'total_amount': order_data.get('total', 0),
                        'marketplace_status': order_data.get('status', ''),
                        'items': order_data.get('items', []),
                        'customer_name': order_data.get('customer', {}).get('name', ''),
                        'customer_phone': order_data.get('customer', {}).get('phone', ''),
                        'delivery_address': order_data.get('address', '')
                    }
                )

        except Exception as e:
            raise Exception(f"Ошибка синхронизации маркетплейса: {str(e)}")

    def sync_delivery(self, integration, client):
        """Синхронизация доставки"""
        try:
            # Получаем статусы заказов
            delivery_orders = DeliveryOrder.objects.filter(
                delivery=integration,
                tracking_number__isnull=False
            )

            for order in delivery_orders:
                try:
                    status_data = client.get_order_status(order.delivery_order_id)

                    order.status = status_data.get('status', order.status)
                    order.sync_data['tracking_history'] = status_data.get('history', [])
                    order.save()

                except Exception as e:
                    self.stdout.write(f"      Ошибка обновления заказа {order.order_id}: {str(e)}")

        except Exception as e:
            raise Exception(f"Ошибка синхронизации доставки: {str(e)}")

    def sync_messenger(self, integration, client):
        """Синхронизация мессенджера"""
        try:
            # Получаем новые сообщения
            updates = client.get_updates()

            for update in updates:
                if 'message' in update:
                    message = update['message']

                    MessengerMessage.objects.get_or_create(
                        messenger=integration,
                        external_id=message['id'],
                        defaults={
                            'chat_id': message['chat']['id'],
                            'direction': 'inbound',
                            'text': message.get('text', ''),
                            'user_id': message['from'].get('id'),
                            'created_at': timezone.now()
                        }
                    )

        except Exception as e:
            raise Exception(f"Ошибка синхронизации мессенджера: {str(e)}")
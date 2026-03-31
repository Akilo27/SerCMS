# moderation/api.py
from django.db import models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json
from .models import (
    IntegrationService, MarketplaceProduct, MarketplaceOrder,
    PaymentTransaction, DeliveryOrder, MessengerMessage
)


@login_required
def products_list_api(request):
    """API для получения списка товаров системы"""
    from moderation.models import Product

    search = request.GET.get('search', '')
    products = Product.objects.filter(is_active=True)

    if search:
        products = products.filter(
            models.Q(name__icontains=search) |
            models.Q(sku__icontains=search)
        )

    products_data = []
    for product in products[:50]:
        products_data.append({
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'price': str(product.price),
            'stock': product.stock
        })

    return JsonResponse({'products': products_data})


@login_required
@require_http_methods(["POST"])
def link_marketplace_product(request):
    """Связывание товара маркетплейса с внутренним товаром"""
    data = json.loads(request.body)
    marketplace_product_id = data.get('marketplace_product_id')
    product_id = data.get('product_id')

    try:
        marketplace_product = MarketplaceProduct.objects.get(id=marketplace_product_id)
        marketplace_product.product_id = product_id
        marketplace_product.save()

        return JsonResponse({'status': 'success'})
    except MarketplaceProduct.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Товар не найден'}, status=404)


@login_required
@require_http_methods(["POST"])
def update_marketplace_price(request):
    """Обновление цены товара на маркетплейсе"""
    data = json.loads(request.body)
    product_id = data.get('product_id')
    price = data.get('price')
    old_price = data.get('old_price')

    try:
        product = MarketplaceProduct.objects.get(id=product_id)
        product.price = price
        if old_price:
            product.old_price = old_price
        product.save()

        # Здесь должна быть логика отправки цены на маркетплейс
        # sync_to_marketplace(product)

        return JsonResponse({'status': 'success'})
    except MarketplaceProduct.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Товар не найден'}, status=404)


@login_required
@require_http_methods(["POST"])
def update_marketplace_stock(request):
    """Обновление остатка товара на маркетплейсе"""
    data = json.loads(request.body)
    product_id = data.get('product_id')
    stock = data.get('stock')

    try:
        product = MarketplaceProduct.objects.get(id=product_id)
        product.stock = stock
        product.save()

        # Здесь должна быть логика отправки остатка на маркетплейс
        # sync_stock_to_marketplace(product)

        return JsonResponse({'status': 'success'})
    except MarketplaceProduct.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Товар не найден'}, status=404)


@login_required
def marketplace_order_detail(request, order_id):
    """Детали заказа маркетплейса"""
    try:
        order = MarketplaceOrder.objects.get(id=order_id)

        return JsonResponse({
            'id': order.id,
            'marketplace_order_id': order.marketplace_order_id,
            'order_date': order.order_date.strftime('%d.%m.%Y %H:%M:%S'),
            'marketplace_status': order.marketplace_status,
            'total_amount': str(order.total_amount),
            'delivery_amount': str(order.delivery_amount),
            'customer_name': order.customer_name,
            'customer_phone': order.customer_phone,
            'customer_email': order.customer_email,
            'delivery_address': order.delivery_address,
            'items': order.items,
            'order_id': order.order_id
        })
    except MarketplaceOrder.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)


@login_required
@require_http_methods(["POST"])
def create_internal_order(request):
    """Создание внутреннего заказа из заказа маркетплейса"""
    data = json.loads(request.body)
    order_id = data.get('order_id')

    try:
        marketplace_order = MarketplaceOrder.objects.get(id=order_id)

        # Здесь должна быть логика создания внутреннего заказа
        # internal_order = Order.objects.create(...)

        marketplace_order.order_id = 1  # Временный ID
        marketplace_order.sync_status = 'synced'
        marketplace_order.save()

        return JsonResponse({'status': 'success', 'order_id': 1})
    except MarketplaceOrder.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Заказ не найден'}, status=404)


@login_required
def payment_transaction_detail(request, transaction_id):
    """Детали платежной транзакции"""
    try:
        transaction = PaymentTransaction.objects.get(id=transaction_id)

        return JsonResponse({
            'id': transaction.id,
            'transaction_id': transaction.transaction_id,
            'external_id': transaction.external_id,
            'amount': str(transaction.amount),
            'currency': transaction.currency,
            'status': transaction.status,
            'status_display': transaction.get_status_display(),
            'payer_name': transaction.payer_name,
            'payer_email': transaction.payer_email,
            'payer_phone': transaction.payer_phone,
            'payment_data': transaction.payment_data,
            'callback_data': transaction.callback_data,
            'created_at': transaction.created_at.strftime('%d.%m.%Y %H:%M:%S'),
            'paid_at': transaction.paid_at.strftime('%d.%m.%Y %H:%M:%S') if transaction.paid_at else None,
            'order_id': transaction.order_id
        })
    except PaymentTransaction.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)


@login_required
@require_http_methods(["POST"])
def refund_payment(request, transaction_id):
    """Возврат платежа"""
    try:
        transaction = PaymentTransaction.objects.get(id=transaction_id)

        if transaction.status != 'success':
            return JsonResponse({'status': 'error', 'message': 'Только успешные платежи можно вернуть'}, status=400)

        # Здесь должна быть логика возврата платежа через API платежной системы
        # refund_result = payment_system.refund(transaction)

        transaction.status = 'refunded'
        transaction.save()

        return JsonResponse({'status': 'success'})
    except PaymentTransaction.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Транзакция не найдена'}, status=404)


@login_required
def messenger_message_detail(request, message_id):
    """Детали сообщения мессенджера"""
    try:
        message = MessengerMessage.objects.get(id=message_id)

        return JsonResponse({
            'id': message.id,
            'text': message.text,
            'direction': message.direction,
            'is_read': message.is_read,
            'attachments': message.attachments,
            'created_at': message.created_at.strftime('%d.%m.%Y %H:%M:%S'),
            'user_id': message.user_id,
            'chat_id': message.chat_id
        })
    except MessengerMessage.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)


@login_required
@require_http_methods(["POST"])
def mark_message_read(request, message_id):
    """Отметить сообщение как прочитанное"""
    try:
        message = MessengerMessage.objects.get(id=message_id)
        message.is_read = True
        message.save()

        return JsonResponse({'status': 'success'})
    except MessengerMessage.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Сообщение не найдено'}, status=404)


@login_required
@require_http_methods(["POST"])
def reply_to_message(request, message_id):
    """Ответ на сообщение"""
    data = json.loads(request.body)
    reply_text = data.get('text', '')

    try:
        original_message = MessengerMessage.objects.get(id=message_id)

        # Создаем исходящее сообщение
        reply = MessengerMessage.objects.create(
            messenger=original_message.messenger,
            direction='outbound',
            text=reply_text,
            chat_id=original_message.chat_id,
            user_id=original_message.user_id,
            external_id=f"reply_{timezone.now().timestamp()}",
            is_read=True,
            sent_at=timezone.now()
        )

        # Здесь должна быть логика отправки сообщения через API мессенджера
        # send_message(original_message.chat_id, reply_text)

        return JsonResponse({'status': 'success', 'message_id': reply.id})
    except MessengerMessage.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Сообщение не найдено'}, status=404)


@login_required
@require_http_methods(["POST"])
def mark_all_messages_read(request):
    """Отметить все сообщения как прочитанные"""
    data = json.loads(request.body)
    messenger_id = data.get('messenger_id')

    MessengerMessage.objects.filter(
        messenger_id=messenger_id,
        direction='inbound',
        is_read=False
    ).update(is_read=True)

    return JsonResponse({'status': 'success'})


@login_required
def delivery_order_detail(request, order_id):
    """Детали заказа доставки"""
    try:
        order = DeliveryOrder.objects.get(id=order_id)

        return JsonResponse({
            'id': order.id,
            'order_id': order.order_id,
            'delivery_order_id': order.delivery_order_id,
            'tracking_number': order.tracking_number,
            'tracking_url': order.tracking_url,
            'status': order.status,
            'status_display': order.get_status_display(),
            'delivery_type': order.delivery_type,
            'delivery_cost': str(order.delivery_cost),
            'estimated_delivery': order.estimated_delivery.strftime('%d.%m.%Y') if order.estimated_delivery else None,
            'actual_delivery': order.actual_delivery.strftime('%d.%m.%Y') if order.actual_delivery else None,
            'recipient_name': order.recipient_name,
            'recipient_phone': order.recipient_phone,
            'recipient_address': order.recipient_address,
            'weight': order.weight,
            'length': order.length,
            'width': order.width,
            'height': order.height,
            'tracking_history': order.sync_data.get('tracking_history', [])
        })
    except DeliveryOrder.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)


@login_required
@require_http_methods(["POST"])
def update_delivery_status(request, order_id):
    """Обновить статус доставки"""
    try:
        order = DeliveryOrder.objects.get(id=order_id)

        # Здесь должна быть логика запроса текущего статуса у службы доставки
        # current_status = delivery_service.get_status(order.tracking_number)

        # Имитация обновления статуса
        order.sync_data['tracking_history'] = order.sync_data.get('tracking_history', [])
        order.sync_data['tracking_history'].append({
            'date': timezone.now().strftime('%d.%m.%Y %H:%M:%S'),
            'status': order.get_status_display(),
            'description': 'Обновление статуса'
        })
        order.save()

        return JsonResponse({'status': 'success'})
    except DeliveryOrder.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Заказ не найден'}, status=404)


@login_required
def integration_log_detail(request, log_id):
    """Детали лога интеграции"""
    from .models import IntegrationLog

    try:
        log = IntegrationLog.objects.select_related('integration').get(id=log_id)

        return JsonResponse({
            'id': log.id,
            'integration_id': log.integration.id,
            'integration_name': log.integration.name,
            'operation': log.operation,
            'operation_display': log.get_operation_display(),
            'status': log.status,
            'status_display': log.get_status_display(),
            'request_data': log.request_data,
            'response_data': log.response_data,
            'error_message': log.error_message,
            'duration': log.duration,
            'duration_formatted': log.get_duration_formatted(),
            'started_at': log.started_at.strftime('%d.%m.%Y %H:%M:%S'),
            'completed_at': log.completed_at.strftime('%d.%m.%Y %H:%M:%S') if log.completed_at else None,
        })
    except IntegrationLog.DoesNotExist:
        return JsonResponse({'error': 'Log not found'}, status=404)
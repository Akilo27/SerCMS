# moderation/signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import IntegrationService, IntegrationLog, MarketplaceProduct


@receiver(post_save, sender=IntegrationService)
def log_integration_change(sender, instance, created, **kwargs):
    """Логирование изменений интеграции"""
    action = 'создана' if created else 'обновлена'

    IntegrationLog.objects.create(
        integration=instance,
        operation='webhook',
        status='success',
        request_data={'action': action},
        response_data={'name': instance.name, 'service_type': instance.service_type},
        duration=0,
        completed_at=timezone.now()
    )


@receiver(pre_delete, sender=IntegrationService)
def log_integration_delete(sender, instance, **kwargs):
    """Логирование удаления интеграции"""
    IntegrationLog.objects.create(
        integration=instance,
        operation='webhook',
        status='success',
        request_data={'action': 'удалена'},
        response_data={'name': instance.name},
        duration=0,
        completed_at=timezone.now()
    )


@receiver(post_save, sender=MarketplaceProduct)
def log_product_sync(sender, instance, created, **kwargs):
    """Логирование синхронизации товара"""
    if not created:
        IntegrationLog.objects.create(
            integration=instance.marketplace,
            operation='sync_products',
            status='success',
            request_data={'product_id': instance.id},
            response_data={'sku': instance.marketplace_sku, 'price': instance.price},
            duration=0,
            completed_at=timezone.now()
        )
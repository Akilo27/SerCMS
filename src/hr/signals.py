from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import HRChangeLog, WorkShift, Schedule
from .middleware import get_current_user
from django.db.models.signals import post_save
from django.utils import timezone
from datetime import time

SKIP_FIELDS = {"id", "created_at", "updated_at", "time_change"}

@receiver(pre_save)
def log_all_changes(sender, instance, **kwargs):
    if sender is HRChangeLog:
        return
    if not instance.pk:
        return
    user = get_current_user()
    if not user or not user.is_authenticated:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    ct = ContentType.objects.get_for_model(sender)
    logs = []  # Создаем список чтобы потом применить сразу все
    for field in instance._meta.fields:
        name = field.name
        if name in SKIP_FIELDS:
            continue
        old_val = getattr(old, name, None)
        new_val = getattr(instance, name, None)
        if old_val != new_val:
            logs.append(HRChangeLog(
                user=user,
                content_type=ct,
                object_id=instance.pk,
                field_name=name,
                old_value=str(old_val),
                new_value=str(new_val),
            ))

    if logs:
        HRChangeLog.objects.bulk_create(logs)


@receiver(post_save, sender=WorkShift)
def update_work_status(sender, instance, **kwargs):
    if instance.time_start and instance.work_status != '2':
        instance.work_status = '2'
        instance.save()


@receiver(post_save, sender=WorkShift)
def create_schedule_on_workshift_create(sender, instance, created, **kwargs):
    if created:
        # Если время не указано, установим значение по умолчанию
        time_start = instance.time_start if instance.time_start else time(0, 0)

        # Создаем объект Schedule с привязкой к пользователю и временем начала
        Schedule.objects.create(
            user=instance.user,
            data_start=instance.date_start,
            time_start=time_start,
            name=f"Смена {instance.user}",
            description=f"Смена пользователя {instance.user}",
        )


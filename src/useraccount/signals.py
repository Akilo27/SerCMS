import string
import random
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from moderation.models import Stopwords
from webmain.models import Comments
from .models import Profile, Company
import hashlib
from django.contrib.auth.signals import user_logged_in

from shop.models import Cart


# Функция для генерации уникального кода
def generate_referral_code():
    return "".join(
        random.choices(string.ascii_letters + string.digits, k=10)
    )  # 10 символов


# Сигнал для генерации referral_code
@receiver(post_save, sender=Profile)
def create_referral_code(sender, instance, created, **kwargs):
    if (
        created and not instance.referral_code
    ):  # Только для новых записей без referral_code
        unique_code = generate_referral_code()

        # Убедимся, что код уникален
        while Profile.objects.filter(referral_code=unique_code).exists():
            unique_code = generate_referral_code()

        instance.referral_code = unique_code
        instance.save()


@receiver(post_save, sender=Profile)
def create_company_for_user(sender, instance, created, **kwargs):
    if (
        created and instance.type == 3
    ):  # Проверяем, что пользователь нового типа (Компания)
        # Создаём компанию, если пользователь новый и типа "Компания"
        company = Company.objects.create(
            name=instance.company_name or "Компания " + str(instance.id),
            director=instance,
        )
        # Добавляем пользователя в компанию
        company.users.add(instance)
        company.save()


@receiver(pre_save, sender=Comments)
def check_stopwords_in_comment(sender, instance, **kwargs):
    """Проверяет комментарий на наличие стоп-слов перед сохранением"""
    if instance.comment:  # Проверяем, что комментарий не пуст
        stopwords = Stopwords.objects.values_list(
            "name", flat=True
        )  # Получаем список стоп-слов

        found_stopwords = {
            word for word in stopwords if word.lower() in instance.comment.lower()
        }

        if found_stopwords:
            instance.publishet = False  # Если есть стоп-слова, не публикуем
        else:
            instance.publishet = True  # Если нет стоп-слов, публикуем


@receiver(user_logged_in)
def assign_cart_to_user(sender, user, request, **kwargs):
    client_ip = request.META.get("REMOTE_ADDR", "")
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()

    cart = Cart.objects.filter(user__isnull=True, browser_key=browser_key).first()
    if cart:
        cart.user = user
        cart.save()

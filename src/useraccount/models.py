from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid
from multiselectfield import MultiSelectField
from django.contrib.sites.models import Site
from django.urls import reverse
import string
import random

from shop.models import Products, Manufacturers
import json



def generate_random_code(length=8):
    # Берём буквы и цифры
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def get_user_dir(instance, filename) -> str:
    extension = filename.split(".")[-1]
    return f"users/user_{instance.id}.{extension}"


class Profile(AbstractUser):
    """Персона"""

    GENDER_CHOICE = [
        (1, "Мужской"),
        (2, "Женский"),
    ]
    TYPE = [
        (0, "Сотрудник"),
        (1, "Обычный"),
        (2, "Юр лицо"),
        (3, "Компания"),
        (4, "Клиент"),
        (5, "Известный клиент"),
    ]
    status = models.BooleanField(default=False, verbose_name="Статус")
    type = models.PositiveSmallIntegerField(
        "Тип пользователя", choices=TYPE, blank=True, null=True, default=1
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(
        blank=True, verbose_name="Телефон", max_length=500, null=True, unique=True
    )
    email = models.EmailField("Email", unique=True)
    avatar = models.FileField(
        upload_to=get_user_dir,
        blank=True,
        null=True,
        verbose_name="Аватар",
        default="default/user-nophoto.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    device_token = models.TextField(
        blank=True, null=True, verbose_name="FCM токен устройства"
    )
    gender = models.PositiveSmallIntegerField(
        "Пол", choices=GENDER_CHOICE, blank=True, null=True, default=1
    )
    birthday = models.DateField(verbose_name="Дата рождения", blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, verbose_name="Город", null=True)
    adresses = models.TextField("Адреса", blank=True, null=True,default='[]')
    middle_name = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Отчество"
    )
    online = models.BooleanField(default=False, verbose_name="Онлайн")
    blocked = models.BooleanField(default=False, verbose_name="Заблокирован")
    deleted = models.BooleanField(default=False, verbose_name="Удален")
    earned = models.PositiveSmallIntegerField(
        verbose_name="Заработано", blank=True, null=True, default=0
    )
    balance = models.PositiveSmallIntegerField(
        verbose_name="Баланс", blank=True, null=True, default=0
    )
    frozen = models.PositiveSmallIntegerField(
        verbose_name="Замороженный баланс", blank=True, null=True, default=0
    )
    bookmark = models.ManyToManyField(Products, verbose_name="Закладки",  blank=True, null=True)
    price_reduction = models.ManyToManyField(Products, verbose_name="Закладки", blank=True, null=True, related_name='price_reduction')
    manufacturers = models.ForeignKey(
        Manufacturers,
        verbose_name="Магазин",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    manufacturers_subscriber = models.ManyToManyField(
        Manufacturers,
        verbose_name="Подписки", related_name='subscriber'
    )
    """Реферальная система"""
    point = models.PositiveSmallIntegerField(
        verbose_name="Баллы", blank=True, null=True, default=0
    )
    referral = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    referral_code = models.CharField(
        max_length=100, blank=True, null=True,default=generate_random_code, verbose_name="Личный код"
    )
    referrale_code = models.CharField(max_length=100, blank=True, null=True, verbose_name='Личный код')

    """Паспортные данные пользователя"""
    passport_issued_by_whom = models.TextField("Кем выдан", blank=True, null=True)
    passport_date_of_issue = models.DateField(
        verbose_name="Дата выдачи", blank=True, null=True
    )
    passport_the_sub_division_code = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Код подрозделения"
    )
    passport_series_and_number = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Серия и номер"
    )
    passport_place_of_birth = models.TextField("Место рождения", blank=True, null=True)
    passport_registration = models.TextField("Прописка", blank=True, null=True)
    passport_image_1 = models.FileField(
        upload_to=get_user_dir,
        blank=True,
        null=True,
        verbose_name="Лицевая часть",
        default="default/user-nophoto.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    passport_image_2 = models.FileField(
        upload_to=get_user_dir,
        blank=True,
        null=True,
        verbose_name="Место прописки",
        default="default/user-nophoto.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )

    """Данные по организации"""
    company_name = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Название организации"
    )
    company_director = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Руководитель"
    )
    company_address = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Юридический адрес"
    )
    company_nalogovaya = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Налоговый орган"
    )
    company_ogrn = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="ОГРН"
    )
    company_inn = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="ИНН"
    )
    company_kpp = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="КПП"
    )
    company_data_registration = models.DateField(
        verbose_name="Дата регистрации", blank=True, null=True
    )
    company_type_activity = models.TextField(
        "Основной вид деятельности", blank=True, null=True
    )
    site = models.ManyToManyField(Site, verbose_name="Сайты", blank=True, default="1")

    def get_absolute_url(self):
        return reverse("persons", kwargs={"slug": self.slug})

    def get_adresses(self):
        """Возвращает список адресов в виде Python-объекта."""
        try:
            return json.loads(self.adresses) if self.adresses else []
        except json.JSONDecodeError:
            return []

    def set_adresses(self, addresses_list):
        """Сохраняет список адресов в формате JSON."""
        self.adresses = json.dumps(addresses_list, ensure_ascii=False)


    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, verbose_name="Название")
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователи",
        blank=True,
        related_name="personalcompany",
    )
    director = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name="Руководитель", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"


class SearchQuery(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.CASCADE, related_name='search_queries'
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    query = models.CharField(max_length=255, db_index=True)
    count = models.PositiveIntegerField(default=0)
    last_searched = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            ('user', 'query'),
            ('session_key', 'query'),
        )
        indexes = [
            models.Index(fields=['-last_searched']),
            models.Index(fields=['query']),
        ]

    def __str__(self):
        return self.query

class PersonalGroups(models.Model):
    TYPE_OPTIONS = (
        (
            "Номера телефонов",
            (
                (
                    "phone_default",
                    "Номер телефона по умолчанию",
                ),
                ("phone", "Остальные номера телефонов"),
            ),
        ),
        (
            "Электроная почта",
            (
                (
                    "email_default",
                    "Почта по умолчанию",
                ),
                ("email", "Остальные почты"),
            ),
        ),
    )
    types = MultiSelectField(
        choices=TYPE_OPTIONS,
        blank=True,
        verbose_name="Доступ",
        default=list,
        null=True,
        max_length=255,  # Добавьте это, чтобы предотвратить ошибку с длиной
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(editable=False)
    name = models.CharField(max_length=150, verbose_name="Название")
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователи",
        blank=True,
        related_name="grouppersonal",
    )
    company = models.ForeignKey(
        Company, verbose_name="Руководитель", on_delete=models.CASCADE
    )
    site = models.ManyToManyField(Site, verbose_name="Сайты", blank=True, default="1")

    def get_types_display(self):
        return ", ".join(dict(self.TYPE_OPTIONS).get(type_id) for type_id in self.types)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"


class Notification(models.Model):
    """Персона"""

    TYPE = [
        (0, "Общее"),
        (1, "Регистрация"),
        (2, "Покупка"),
        (3, "Сбросить пароль"),
        (4, "Поддержка"),
    ]
    type = models.PositiveSmallIntegerField("Тип", choices=TYPE, blank=False, default=0)
    STATUS = [
        (1, "Не прочитан"),
        (2, "Прочитан"),
    ]
    status = models.PositiveSmallIntegerField(
        "Статус", choices=STATUS, blank=False, default=1
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Пользователь", on_delete=models.CASCADE
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={
            "model__in": (
                "blogs",
                "pages",
                "categorysblogs",
                "tagsblogs",
            )
        },
        blank=True,
        null=True,
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField("Время отправки", auto_now_add=True)
    title = models.TextField(verbose_name="Заголовок", blank=True, null=True)
    message = models.TextField(verbose_name="Сообщение", blank=True, null=True)
    image = models.FileField(
        upload_to=get_user_dir,
        blank=True,
        null=True,
        verbose_name="Изображение",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомление"


class Withdrawal(models.Model):
    """Выплаты"""
    manufacturers = models.ForeignKey(
                Manufacturers,
                on_delete=models.CASCADE,
                verbose_name="Магазин",
                blank=True,
                null=True,
            )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Пользователь", on_delete=models.CASCADE
    )
    amount = models.IntegerField("Сумма", blank=True, null=True)
    TYPE_PAYMENT_CHOICES = [
        (0, "Пополнение"),
        (1, "Списание"),
    ]
    type_payment = models.SmallIntegerField(
        verbose_name="Пополнение/Списание", choices=TYPE_PAYMENT_CHOICES, default=0
    )
    TYPE_CHOICES = [
        (0, "Деньги"),
        (1, "Баллы"),
    ]
    type = models.SmallIntegerField(
        verbose_name="Пополнение/Списание", choices=TYPE_CHOICES, default=0
    )
    create = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Выплата"
        verbose_name_plural = "Выплаты"


class Cards(models.Model):
    STATUS = [
        (1, "Активная"),
        (2, "Не активная"),
    ]
    card = models.CharField(verbose_name="Карта", max_length=19)
    date = models.DateTimeField("Дата обновления карты", auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="cardowner",
    )
    status = models.PositiveSmallIntegerField(
        "Статус", default=2, choices=STATUS, blank=False
    )

    def str(self):
        return f"{self.card}"

    def save(self, *args, **kwargs):
        self.card = self.card.replace("-", "")
        formatted_card = "-".join(
            [self.card[i : i + 4] for i in range(0, len(self.card), 4)]
        )
        self.card = formatted_card
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Банковская карта"
        verbose_name_plural = "Банковские карты"


class PersonalCards(models.Model):
    STATUS = [
        (1, "Активная"),
        (2, "Не активная"),
    ]
    TYPE = [
        (1, "Стандарт"),
        (2, "Професиональная"),
        (3, "Вип"),
    ]
    card = models.CharField(verbose_name="Карта", max_length=19)
    discount = models.CharField(verbose_name="Скидка", max_length=19)
    date = models.DateTimeField("Дата обновления карты", auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    status = models.PositiveSmallIntegerField(
        "Статус", default=2, choices=STATUS, blank=False
    )
    type = models.PositiveSmallIntegerField("Тип", default=1, choices=TYPE, blank=False)

    def str(self):
        return f"{self.card}"

    class Meta:
        verbose_name = "Личная карта"
        verbose_name_plural = "Личные карты"


class Bookmarks(models.Model):
    """Закладка"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Пользователь", on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Название",
        null=True,
        default="По умолчанию",
    )
    informationjon = models.TextField(
        verbose_name="Информация",
        help_text='Образец: [{"type": products, "id": [123, 1231edf, 4534fvdvdf]}]',
    )

    class Meta:
        verbose_name = "Закладка"
        verbose_name_plural = "Закладки"

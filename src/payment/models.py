from random import randrange
from shop.models import SelectedProduct
from django.contrib.sites.models import Site

from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator


# Create your models here.
class PaymentType(models.Model):
    """Страницы"""

    TYPE = [
        (0, "ЮКасса"),
        (1, "ЮМани"),
        (2, "Тинькоф"),
        (3, "Gateway"),
        (4, "АльфаБанк"),
        (5, "СберБанк"),
        (6, "ВТБ"),
        (7, "СовкомБанк"),
        (8, "ПочтаБанк"),
        (9, "FreedomPay"),
        (10, "PayTR"),
    ]
    type = models.PositiveSmallIntegerField("Тип", choices=TYPE, blank=False, default=1)
    key_1 = models.TextField("Первый ключ (public key)")
    key_2 = models.CharField("Второй ключ (secret key)", max_length=550)
    shop_key = models.CharField("Ключ магазина (shop key)", max_length=550)
    content = models.TextField(blank=True, null=True, verbose_name="Описание")
    turn_on = models.BooleanField("Включить", default=False)
    image = models.FileField(
        upload_to="payment_type/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Изображение",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )

    class Meta:
        verbose_name = "Способ оплаты"
        verbose_name_plural = "Способы оплаты"


class Order(models.Model):
    PAYMENT_TYPE = [
        (1, "Оплата не прошла"),
        (2, "Оплачено"),
    ]
    STATUS = [
        (1, "Комплектуется"),
        (2, "Отправлен"),
    ]
    reviews = models.BooleanField("Оставлен отзыв", default=False)
    type = models.PositiveSmallIntegerField(
        "Тип оплаты", choices=PAYMENT_TYPE, blank=False, default=1
    )
    status = models.PositiveSmallIntegerField(
        "Статус", choices=STATUS, blank=False, default=1
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_DEFAULT,
        blank=True,
        null=True,
        verbose_name="Пользователь",
        default=None,
    )
    offline = models.BooleanField(default=False)
    created_timestamp = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания заказа"
    )
    phone_number = models.CharField(max_length=20, verbose_name="Номер телефона", db_index=True)
    key = models.CharField(verbose_name="Ключ", max_length=32, unique=True, blank=True, db_index=True)
    customer_name = models.CharField(max_length=200, verbose_name="Имя")
    customer_surname = models.CharField(max_length=200, verbose_name="Фамилия")
    customer_email = models.CharField(max_length=200, verbose_name="Адрес эл почты")
    sflat = models.CharField(
        max_length=200,
        verbose_name="Квартира",
        null=True,
        blank=True,
    )
    sfloor = models.CharField(
        max_length=200,
        verbose_name="Этаж",
        null=True,
        blank=True,
    )
    porch = models.CharField(
        max_length=200,
        verbose_name="Подьезд",
        null=True,
        blank=True,
    )
    user_comment = models.TextField(
        verbose_name="Комментарий к доставке от пользователя ",
        null=True,
        blank=True,
    )
    requires_delivery = models.BooleanField(
        default=False, verbose_name="Требуется доставка"
    )
    delivery_address = models.TextField(
        null=True, blank=True, verbose_name="Адрес доставки"
    )
    longitude = models.TextField(null=True, blank=True, verbose_name="Адрес longitude")
    latitude = models.TextField(null=True, blank=True, verbose_name="Адрес latitude")
    city = models.TextField(null=True, blank=True, verbose_name="Адрес Город")
    adress = models.TextField(null=True, blank=True, verbose_name="Адрес Дома")
    selectedproduct = models.ManyToManyField(
        SelectedProduct, verbose_name="Выбранные Товары"
    )
    amount = models.PositiveSmallIntegerField(default=0, verbose_name="Сумма")
    delivery_price = models.PositiveSmallIntegerField(
        default=0, verbose_name="Сумма за доставку"
    )
    all_amount = models.PositiveIntegerField(default=0, verbose_name="Общая сумма")
    key = models.CharField(verbose_name="Ключ", max_length=32, unique=True, blank=True)
    purchase_url = models.TextField(verbose_name="Покупка юрл", blank=True, null=True)
    site = models.ForeignKey(
        Site, verbose_name="Сайты", on_delete=models.CASCADE, blank=True, null=True
    )
    payload = models.TextField(null=True, blank=True, verbose_name="Payload")
    is_payload_set = models.BooleanField(default=False)
    claim_id = models.TextField(null=True, blank=True, verbose_name="claim_id")
    is_claim_id_set = models.BooleanField(
        default=False, verbose_name="claim_id_statsus"
    )
    mail_send = models.BooleanField(default=False, verbose_name="mail_send")

    def save(self, *args, **kwargs):
        loop_num = 0
        unique = False
        while not self.key and not unique:
            if loop_num < settings.RANDOM_URL_MAX_TRIES:
                new_key = ""
                for i in range(settings.RANDOM_URL_LENGTH):
                    new_key += settings.RANDOM_URL_CHARSET[
                        randrange(0, len(settings.RANDOM_URL_CHARSET))
                    ]
                if not Order.objects.filter(key=new_key):
                    self.key = new_key
                    unique = True
                loop_num += 1
            else:
                raise ValueError("Couldn't generate a unique code.")

        if self.is_payload_set:
            # Если payload уже установлен, пропускаем его обновление
            kwargs["update_fields"] = kwargs.get("update_fields", [])
            if "payload" not in kwargs["update_fields"]:
                kwargs["update_fields"].append("payload")
            if "is_payload_set" not in kwargs["update_fields"]:
                kwargs["update_fields"].append("is_payload_set")

        super(Order, self).save(*args, **kwargs)

    def is_paid(self):
        """Проверяет, оплачен ли заказ"""
        return self.type == 2

    def get_payment_status_display(self):
        """Возвращает текстовое представление статуса оплаты"""
        return dict(self.PAYMENT_TYPE).get(self.type, "Неизвестно")


    def __str__(self):
        return f"Заказ № {self.pk} | Покупатель {self.customer_name} {self.customer_surname}"

    class Meta:
        db_table = "order"
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

class PurchasedProduct(models.Model):
    products = models.ForeignKey(
        SelectedProduct,  # замените на `Product`, если нужен сам товар
        on_delete=models.CASCADE,
        verbose_name="Продукт"
    )
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_DEFAULT,
        blank=True,
        null=True,
        verbose_name="Пользователь",
        default=None,
    )

    def __str__(self):
        return f"{self.product} x{self.quantity}"

    class Meta:
        verbose_name = "Купленный товар"
        verbose_name_plural = "Купленные товары"

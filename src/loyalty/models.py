import string
import random
from django.db import models
from django.conf import settings
from django.utils import timezone
from useraccount.models import Profile
from shop.models import Products, Categories, Brands,Manufacturers
from payment.models import Order


def generate_random_code(length=8):
    # Берём буквы и цифры
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


# Create your models here.
class PersonalPromotion(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name="Пользователь")
    is_active = models.BooleanField(default=True, verbose_name="Активирован")
    valid_until = models.DateTimeField(null=True, blank=True, verbose_name="Дата жизни")
    manager = models.BooleanField(default=True, name='Менеджер')
    product = models.ForeignKey(Products, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Товар")
    category = models.ForeignKey(Categories, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Категория")
    brand = models.ForeignKey(Brands, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Бренд")

    def __str__(self):
        return self.name




def generate_coupon_code(length=10):
    """Генерация случайного кода для купона"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


class Coupon(models.Model):
    description = models.TextField(blank=True, verbose_name="Описание")
    STATUS_CHOICES = [
        (0, "Не активирован"),
        (1, "Активирован"),
    ]
    code = models.CharField("Код купона", max_length=12, unique=True, default=generate_coupon_code, editable=False)
    valid_until = models.DateTimeField(null=True, blank=True, verbose_name="Дата жизни")
    status = models.PositiveSmallIntegerField("Статус", choices=STATUS_CHOICES, default=0)
    email = models.EmailField("Email", blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, blank=True,null=True,verbose_name="Заказ",)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True,null=True,verbose_name="Пользователь",)
    product = models.ForeignKey(Products,on_delete=models.CASCADE,blank=True,null=True, verbose_name="Товар",)
    manufacturers = models.ForeignKey( Manufacturers, on_delete=models.CASCADE,blank=True,null=True,verbose_name="Магазин", )
    category = models.ForeignKey(Categories, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Категория")
    brand = models.ForeignKey(Brands, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Бренд")
    discount = models.DecimalField(  "Скидка (%)", max_digits=5, decimal_places=2, default=0)
    amount = models.DecimalField("Сумма скидки", max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    activated_at = models.DateTimeField("Дата активации", blank=True, null=True)

    class Meta:
        verbose_name = "Купон"
        verbose_name_plural = "Купоны"

    def __str__(self):
        return f"{self.code} ({self.get_status_display()})"

    def activate(self):
        """Метод активации купона"""
        self.status = 1
        self.activated_at = timezone.now()
        self.save()

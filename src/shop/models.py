import os
import random
import string

from django.db import models
from django.conf import settings
from django.urls import reverse
from ckeditor.fields import RichTextField
from django.utils import timezone
from django.conf import settings
from io import BytesIO
from django.core.files.base import ContentFile
# from moderation.models import Stopwords
from django.core.validators import FileExtensionValidator
from django.contrib.sites.models import Site
import uuid, qrcode
from qrcode.constants import ERROR_CORRECT_M
from uuid import uuid4
from chat.models import Chat
from decimal import Decimal
from django.utils import timezone


"""Товары"""
class ManufacturersIncome(models.Model):
    data = models.DateField(blank=True, null=True, verbose_name='Дата')
    manufacturers = models.ForeignKey(
                "Manufacturers",
                on_delete=models.CASCADE,
                verbose_name="Магазин",
                blank=True,
                null=True,
            )
    price = models.DecimalField(
        default=0.00,
        max_digits=11,
        decimal_places=2,  # Было 0
        verbose_name="Цена",
    )
    create = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = "Доход на магазин"
        verbose_name_plural = "Доход на магазин"

class ManufacturersExpenseType(models.Model):
    name = models.CharField(max_length=150,verbose_name='Название')

    def __str__(self):
        return self.name


    class Meta:
        verbose_name = "Тип расхода на магазин"
        verbose_name_plural = "Типы расходов на магазины"

class ManufacturersExpense(models.Model):
    data = models.DateField(blank=True, null=True, verbose_name='Дата')
    manufacturersexpense = models.ForeignKey(
                "ManufacturersExpenseType",
                on_delete=models.CASCADE,
                verbose_name="Расходник",
                blank=True,
                null=True,
            )
    manufacturers = models.ForeignKey(
                "Manufacturers",
                on_delete=models.CASCADE,
                verbose_name="Магазин",
                blank=True,
                null=True,
            )
    price = models.DecimalField(
        default=0.00,
        max_digits=11,
        decimal_places=2,  # Было 0
        verbose_name="Цена",
    )

    count = models.PositiveIntegerField(blank=True,null=True)
    create = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = "Расход на магазин"
        verbose_name_plural = "Расходы на магазин"

class Manufacturers(models.Model):
    verefi = models.BooleanField(default=True, blank=True, null=True, verbose_name="Верефицированый")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True,  null=True, related_name="owner", verbose_name="Владелец", )
    assistant = models.ManyToManyField(  settings.AUTH_USER_MODEL, related_name="assistant", verbose_name="Пользователи",  )
    shop_id = models.CharField(max_length=64,   null=True, blank=True)
    token = models.CharField(max_length=128, null=True, blank=True)
    xml_link = models.CharField(max_length=64, unique=True,  null=True, blank=True)
    name = models.CharField(max_length=150, verbose_name="Название")
    slug = models.SlugField(
        max_length=200, unique=True, blank=True, null=True, verbose_name="URL"
    )
    review_rating = models.PositiveIntegerField(
        default=1, verbose_name="Оценка отзывов"
    )

    image = models.FileField(
        upload_to="manufacturers/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Изображение",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    cover = models.FileField(
        upload_to="manufacturers/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Обложка",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    previev = models.FileField(
        upload_to="blogs/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Превью",
        default="default/imagegallery/imagegellery_images.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    title = models.CharField(
        max_length=150, verbose_name="Мета-заголовок", blank=True, null=True
    )
    metadescription = models.TextField(
        blank=True, null=True, verbose_name="Мета-описание"
    )
    propertytitle = models.CharField(
        verbose_name="Мета-заголовок ссылки",
        max_length=150,
        blank=True,
        null=True,
    )
    propertydescription = models.CharField(
        verbose_name="Мета-описание ссылки",
        max_length=255,
        blank=True,
        null=True,
    )
    email = models.CharField(
        blank=True, verbose_name="Email", max_length=500, null=True
    )
    phone = models.CharField(
        blank=True, verbose_name="Телефон", max_length=500, null=True
    )
    company_name = models.CharField(
        blank=True, verbose_name="Название компании", max_length=500, null=True
    )
    company_chart = models.CharField(
        blank=True, verbose_name="График компании", max_length=500, null=True
    )
    company_inn = models.CharField(
        blank=True, verbose_name="ИНН организации или ИП", max_length=500, null=True
    )
    company_director = models.CharField(
        blank=True, verbose_name="ФИО директора", max_length=500, null=True
    )
    company_adress = models.CharField(
        blank=True, verbose_name="Адрес", max_length=500, null=True
    )
    company_coordinates = models.CharField(
        blank=True, verbose_name="Адрес", max_length=500, null=True
    )

    categories = models.ManyToManyField(
        "Categories", verbose_name="Категория", blank=True
    )
    site = models.ManyToManyField(Site, verbose_name="Сайты")
    create = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    update = models.DateTimeField(auto_now=True, blank=True, null=True)

    def get_absolute_url(self):
        return reverse("shop:manufacturers", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.shop_id:
            self.shop_id = uuid.uuid4().hex[:16]
        if not self.token:
            self.token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    class Meta:
        db_table = "manufacturers"
        verbose_name = "Производитель"
        verbose_name_plural = "Производители"

    def __str__(self):
        return self.name

class ProductExpensePurchase(models.Model):
    productexpenseposition = models.ForeignKey(
                "ProductExpensePosition",
                on_delete=models.CASCADE,
        related_name='productexpenseposition',
                verbose_name="Расходник",
                blank=True,
                null=True,
            )
    manufacturers = models.ForeignKey(
                "Manufacturers",
                on_delete=models.CASCADE,
                verbose_name="Магазин",
                blank=True,
                null=True,
            )

    count = models.PositiveIntegerField(blank=True,null=True)
    data = models.DateField( blank=True, null=True, verbose_name='Дата')
    price = models.PositiveIntegerField(blank=True,null=True)
    data = models.DateField(blank=True, null=True, verbose_name='Дата')
    create = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = "Закупка расхода на товар"
        verbose_name_plural = "Закупки расходо на товар"


class ProductExpensePosition(models.Model):
    name = models.CharField(max_length=150,verbose_name='Название')
    count = models.PositiveIntegerField(blank=True,null=True)

    class Meta:
        verbose_name = "Расход"
        verbose_name_plural = "Расходы"

    def __str__(self):
        return self.name


class ProductExpense(models.Model):
    product = models.ForeignKey(
        "Products",
        on_delete=models.CASCADE,
        verbose_name="Продукт",
        blank=True,
        null=True,
    )
    productexpenseposition = models.ForeignKey(
        "ProductExpensePosition",
        on_delete=models.CASCADE,
        verbose_name="Расходник",
        blank=True,
        null=True,
    )
    count = models.PositiveIntegerField(blank=True,null=True)

    class Meta:
        verbose_name = "Расход на товар"
        verbose_name_plural = "Расходы на товар"


class Brands(models.Model):
    name = models.CharField(max_length=150, verbose_name="Название")
    slug = models.SlugField(
        max_length=200, unique=True, blank=True, null=True, verbose_name="URL"
    )
    image = models.FileField(
        upload_to="manufacturers/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Изображение",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    cover = models.FileField(
        upload_to="manufacturers/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Обложка",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    previev = models.FileField(
        upload_to="blogs/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Превью",
        default="default/imagegallery/imagegellery_images.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    title = models.CharField(
        max_length=150, verbose_name="Мета-заголовок", blank=True, null=True
    )
    metadescription = models.TextField(
        blank=True, null=True, verbose_name="Мета-описание"
    )
    propertytitle = models.CharField(
        verbose_name="Мета-заголовок ссылки",
        max_length=150,
        blank=True,
        null=True,
    )
    propertydescription = models.CharField(
        verbose_name="Мета-описание ссылки",
        max_length=255,
        blank=True,
        null=True,
    )



    class Meta:
        verbose_name = "Производитель"
        verbose_name_plural = "Производители"

    def __str__(self):
        return self.name


class ApplicationsProducts(models.Model):
    """Заявка"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    create = models.DateTimeField(auto_now=True, blank=True, null=True)
    products = models.ForeignKey(
        "Products",
        on_delete=models.CASCADE,
        verbose_name="Образец Продукта",
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Пользователь",
    )
    email = models.CharField(
        blank=True, verbose_name="Email", max_length=500, null=True
    )
    phone = models.CharField(
        blank=True, verbose_name="Телефон", max_length=500, null=True
    )
    content = models.TextField(blank=True, null=True, verbose_name="Описание")

    def __str__(self):
        return self.email if self.email else "Без email"

    class Meta:
        verbose_name = "Заявка продукта"
        verbose_name_plural = "Заявки продукта"


class Categories(models.Model):
    name = models.CharField(max_length=150, verbose_name="Название")
    slug = models.SlugField(
        max_length=200, unique=True, blank=True, null=True, verbose_name="URL"
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    parent = models.ForeignKey(
        "self",
        related_name="children",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Родитель",
    )
    cover = models.FileField(
        "Обложка категории",
        upload_to="category/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    icon = models.FileField(
        "Иконка категории",
        upload_to="category/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    image = models.FileField(
        "Картинка категории",
        upload_to="category/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    previev = models.FileField(
        upload_to="category/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Превью",
        default="default/imagegallery/imagegellery_images.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    title = models.CharField(
        verbose_name="Мета-заголовок",
        max_length=150,
        blank=True,
        null=True,
    )
    metadescription = models.CharField(
        verbose_name="Мета-описание",
        max_length=255,
        blank=True,
        null=True,
    )
    propertytitle = models.CharField(
        verbose_name="Мета-заголовок ссылки",
        max_length=150,
        blank=True,
        null=True,
    )
    propertydescription = models.CharField(
        verbose_name="Мета-описание ссылки",
        max_length=255,
        blank=True,
        null=True,
    )
    publishet = models.BooleanField("Опубликован", default=False)
    site = models.ManyToManyField(Site, verbose_name="Сайты", blank=True, default="1")
    products_rekomendet = models.ManyToManyField(
        "Products", verbose_name="Товары", blank=True
    )
    count_product = models.PositiveSmallIntegerField(
        "Количество товаров", blank=False, default=1
    )
    create = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    update = models.DateTimeField(auto_now=True, blank=True, null=True)

    def get_absolute_url(self):
        return reverse("shop:categories", kwargs={"slug": self.slug})


    def get_parent_categories(self, include_self=True):
        """
        Получить все родительские категории (включая текущую)
        """
        categories = set()
        current = self

        if include_self:
            categories.add(current)

        while current.parent:
            categories.add(current.parent)
            current = current.parent

        return categories

    def get_all_children(self, include_self=True):
        """
        Получить все дочерние категории (включая текущую)
        """
        categories = set()
        if include_self:
            categories.add(self)

        for child in self.children.all():
            categories.add(child)
            categories.update(child.get_all_children(include_self=False))

        return categories

    def get_related_categories(self):
        """
        Получить все связанные категории (текущая, дочерние и родительские)
        """
        related_categories = set()

        # Добавляем текущую категорию и ее дочерние
        related_categories.update(self.get_all_children(include_self=True))

        # Добавляем родительские категории
        related_categories.update(self.get_parent_categories(include_self=False))

        return related_categories


    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class ProductsGallery(models.Model):
    """Изображения продуктов"""

    create = models.DateTimeField(auto_now=True, blank=True, null=True)
    position = models.PositiveIntegerField(default=0, verbose_name="Позиция")
    image = models.FileField(
        "Изображение",
        upload_to="product/%Y/%m/%d/",
        blank=True,
        null=True,
        default="default/product-nophoto.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    image_hash = models.CharField(max_length=32, blank=True, null=True)
    products = models.ForeignKey(
        to="Products", on_delete=models.CASCADE, related_name="productsgallery_set", verbose_name="Образец Продукта"
    )

    class Meta:
        ordering = ['position']
        verbose_name = "Изображение продукта"
        verbose_name_plural = "Изображения продуктов"

    def get_image_url(self):
        return self.image.url if self.image else ""


class Variable(models.Model):
    FILTRETYPE = [
        (1, "Чекбокс"),
        (2, "Выподающий"),
        (3, "Числовой"),
    ]
    type = models.PositiveSmallIntegerField(
        "Тип фильтра", choices=FILTRETYPE, blank=False, default=1
    )
    VARIABLETYPE = [
        (1, "Участвовать в фильтре"),
        (2, "Участвовать в вариаации"),
        (3, "Оба"),
    ]
    variabletype = models.PositiveSmallIntegerField(
        "Тип фильтра", choices=VARIABLETYPE, blank=False, default=1
    )
    VARIABLESTYPE = [
        (1, "Показывать в характеристиках"),
        (2, "Показывать как описание"),
        (3, "Оба"),
    ]
    variablestype = models.PositiveSmallIntegerField(
        "Вариант отображения", choices=VARIABLESTYPE, blank=False, default=1
    )
    slug = models.SlugField(
        max_length=500, unique=True, blank=True, null=True, verbose_name="URL"
    )
    name = models.CharField(max_length=150, unique=True, verbose_name="Название")
    site = models.ManyToManyField(Site, verbose_name="Сайты")
    price = models.DecimalField(
        default=0.00,
        max_digits=11,
        decimal_places=2,  # Было 0
        verbose_name="Цена",
    )

    class Meta:
        db_table = "variable"
        verbose_name = "Вариация"
        verbose_name_plural = "Вариации"

    def __str__(self):
        return self.name


class Atribute(models.Model):
    name = models.CharField(max_length=150, verbose_name="Название")
    variable = models.ForeignKey(
        to=Variable, on_delete=models.CASCADE, verbose_name="Вариация"
    )
    slug = models.SlugField(max_length=500, blank=True, null=True, verbose_name="URL")
    content = models.TextField(blank=True, null=True, verbose_name="Контент")
    image = models.FileField(
        "Изображение",
        upload_to="product/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    create = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        db_table = "atribute"
        verbose_name = "Атрибут"
        verbose_name_plural = "Атрибуты"

    def __str__(self):
        return f"{self.variable} - {self.name}"


class ProductsCloud(models.Model):
    TYPE = [
        (1, "Общедоступный"),
        (2, "Индивидуальный"),
    ]
    STATUS = [
        (1, "Подготавливается"),
        (2, "Доступен для скачивания"),
    ]
    type = models.PositiveIntegerField(
        "Тип", choices=TYPE, blank=True, null=True, default=1
    )
    status = models.PositiveIntegerField(
        "Статус", choices=STATUS, blank=True, null=True, default=1
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    products = models.ForeignKey(
        "Products", on_delete=models.CASCADE, verbose_name="Образец Продукта"
    )
    link = models.TextField(blank=True, null=True, verbose_name="ССылка")
    file = models.FileField(
        "Файл", upload_to="product_arhive/%Y/%m/%d/", blank=True, null=True
    )

    class Meta:
        verbose_name = "Файл продукта"
        verbose_name_plural = "Файлы продуктов"


class Valute(models.Model):
    language = models.CharField(
        max_length=500,
        verbose_name="Язык",
        blank=True,
        null=True,
    )
    name = models.CharField(
        max_length=500,
        verbose_name="Название",
        blank=True,
        null=True,
    )
    key = models.CharField(max_length=500, verbose_name="Код")
    icon_code = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="Код иконки"
    )
    icon_image = models.FileField(
        "Изображение",
        upload_to="product/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    default = models.BooleanField(
        default=True, blank=True, null=True, verbose_name="По умолчанию"
    )
    relationship = models.DecimalField(
        max_digits=10, decimal_places=4, verbose_name="Соотношение"
    )
    allowance = models.PositiveSmallIntegerField(default=0, verbose_name="Наценка")
    create = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ключ - {self.key}"

    class Meta:
        verbose_name = "Валюта"
        verbose_name_plural = "Валюты"


def product_image_path(instance, filename):
    # Извлекаем имя файла без расширения
    filename_without_ext, ext = os.path.splitext(filename)

    # Устанавливаем постоянный путь для каждого продукта, например, по id
    return f"product/{instance.id}/{filename_without_ext}{ext}"


class ProductsPrice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    price = models.DecimalField(
        default=0.00,
        max_digits=11,
        decimal_places=2,  # Было 0
        verbose_name="Цена",
    )
    wholesale_price = models.DecimalField(
        default=0.00, max_digits=11, decimal_places=0, verbose_name="Оптовая цена"
    )
    discount = models.DecimalField(
        default=0.00, max_digits=4, decimal_places=2, verbose_name="Скидка в %"
    )
    product = models.ForeignKey(
        to="Products",
        on_delete=models.CASCADE,
        verbose_name="Товар",
        related_name="products_prices",
        blank=True,
        null=True,
    )
    create = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = "Стоимость"
        verbose_name_plural = "Стоимости"

class ProductsPriceSeller(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    price = models.DecimalField(
        default=0.00,
        max_digits=11,
        decimal_places=2,  # Было 0
        verbose_name="Цена",
    )
    wholesale_price = models.DecimalField(
        default=0.00, max_digits=11, decimal_places=0, verbose_name="Оптовая цена"
    )
    discount = models.DecimalField(
        default=0.00, max_digits=4, decimal_places=2, verbose_name="Скидка в %"
    )
    product = models.ForeignKey(
        to="Products",
        on_delete=models.CASCADE,
        verbose_name="Товар",
        related_name="products_prices_seller",
        blank=True,
        null=True,
    )
    create = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = "Стоимость продавца"
        verbose_name_plural = "Стоимости продавцов"

class ProductsPriceOld(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    price = models.DecimalField(
        default=0.00,
        max_digits=11,
        decimal_places=2,  # Было 0
        verbose_name="Цена",
    )
    wholesale_price = models.DecimalField(
        default=0.00, max_digits=11, decimal_places=0, verbose_name="Оптовая цена"
    )
    discount = models.DecimalField(
        default=0.00, max_digits=4, decimal_places=2, verbose_name="Скидка в %"
    )
    product = models.ForeignKey(
        to="Products",
        on_delete=models.CASCADE,
        verbose_name="Товар",
        related_name="products_prices_old",
        blank=True,
        null=True,
    )
    create = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = "Старая стоимость"
        verbose_name_plural = "Старые стоимости"


class CostPrice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    price = models.DecimalField(
        default=0.00,
        max_digits=11,
        decimal_places=2,  # Было 0
        verbose_name="Цена",
    )
    wholesale_price = models.DecimalField(
        default=0.00, max_digits=11, decimal_places=0, verbose_name="Оптовая цена"
    )
    discount = models.DecimalField(
        default=0.00, max_digits=4, decimal_places=2, verbose_name="Скидка в %"
    )
    product = models.ForeignKey(
        to="Products",
        on_delete=models.CASCADE,
        verbose_name="Товар",
        related_name="cost_prices",
        blank=True,
        null=True,
    )
    create = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = "Стоимость"
        verbose_name_plural = "Стоимости"

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    blocked = models.BooleanField(default=False, verbose_name="Заблокирован")

    def __str__(self):
        status = " (заблокирован)" if self.blocked else ""
        return f"{self.name}{status}"

class Products(models.Model):
    TYPE = [
        (1, "Обычный"),
        (2, "Вариативный + Облачный"),
        (3, "Вариативный"),
        (4, "Облачный"),
    ]
    TYPECHOICE = [
        (1, "Обычный"),
        (2, "Вес"),
        (3, "Упаковка"),
    ]
    posted = models.BooleanField(default=False,verbose_name='опубликован')
    type = models.PositiveIntegerField(
        "Тип продукта", choices=TYPE, blank=False, default=1
    )
    typeofchoice = models.PositiveIntegerField(
        "Тип габарита", choices=TYPECHOICE, blank=False, default=1
    )
    position = models.PositiveIntegerField(default=0, blank=True,null=True, verbose_name="Позиция")
    tags = models.ManyToManyField(Tag, blank=True, related_name='Тэги')
    expenses = models.ManyToManyField(ProductExpense,blank=True, related_name="Расходы")
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(
        max_length=500, unique=True, blank=True, null=True, verbose_name="URL"
    )
    quantity = models.PositiveIntegerField(default=0, verbose_name="Количество")
    review_rating = models.PositiveIntegerField(
        default=0, verbose_name="Оценка отзывов"
    )
    review_count = models.PositiveIntegerField(
        default=0, verbose_name="Количество отзывов"
    )
    review_all_sum = models.PositiveIntegerField(
        default=0, verbose_name="Общая сумма отзывов"
    )
    image = models.FileField(
        "Изображение",
        upload_to=product_image_path,
        blank=True,
        null=True,
        default="default/product-nophoto.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    name = models.CharField(
        max_length=500,
        help_text="ссылка по которой будет доступен",
        verbose_name="Название",
    )
    qr_code = models.ImageField(
        upload_to="products/qrcodes/%Y/%m/",
        blank=True, null=True,
        verbose_name="QR-код"
    )

    article = models.CharField(
        max_length=400,
        verbose_name="Артикул",
        unique=True,
        blank=True,
        null=True,
    )
    fragment = RichTextField(
        max_length=250, blank=True, null=True, verbose_name="отрывок"
    )
    description = RichTextField(blank=True, null=True, verbose_name="Описание")
    variable_json = models.TextField(
        blank=True, null=True, verbose_name="Вариации", default="[]"
    )
    previev = models.FileField(
        upload_to="blogs/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Превью",
        default="default/imagegallery/imagegellery_images.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    title = models.CharField(
        max_length=150, verbose_name="Мета-заголовок", blank=True, null=True
    )
    metadescription = models.TextField(
        blank=True, null=True, verbose_name="Мета-описание"
    )
    propertytitle = models.CharField(
        verbose_name="Мета-заголовок ссылки",
        max_length=150,
        blank=True,
        null=True,
    )
    propertydescription = models.CharField(
        verbose_name="Мета-описание ссылки",
        max_length=255,
        blank=True,
        null=True,
    )
    category = models.ManyToManyField(to=Categories, verbose_name="Категория")
    manufacturers = models.ManyToManyField(
        to=Manufacturers,
        verbose_name="Производитель",
    )
    brand = models.ForeignKey(
        to=Brands,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Бренд",
    )

    price_old = models.DecimalField(
        max_digits=11, decimal_places=2, default=0.00, verbose_name="Старая цена"
    )
    price_item_old = models.ForeignKey(
        to=ProductsPriceOld,
        on_delete=models.CASCADE,
        verbose_name="Старая цена товара",
        blank=True,
        null=True,
    )
    price_seller = models.DecimalField(
        max_digits=11, decimal_places=2, default=0.00, verbose_name="Цена продавца"
    )
    price_item_seller = models.ForeignKey(
        to=ProductsPriceSeller,
        on_delete=models.CASCADE,
        verbose_name="Цена продавца",
        blank=True,
        null=True,
    )

    price = models.DecimalField(
        max_digits=11, decimal_places=2, default=0.00, verbose_name="Цена"
    )
    price_item = models.ForeignKey(
        to=ProductsPrice,
        on_delete=models.CASCADE,
        verbose_name="Цена товара",
        blank=True,
        null=True,
    )
    costprice = models.DecimalField(
        max_digits=11,
        decimal_places=2,
        default=0.00,
        verbose_name="Цена себестоимости",
        blank=True,
        null=True,
    )
    costprice_item = models.ForeignKey(
        to=CostPrice,
        on_delete=models.CASCADE,
        verbose_name="Цена себестоимости",
        blank=True,
        null=True,
    )
    valute = models.ForeignKey(
        to=Valute,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Валюта",
    )
    manufacturer_identifier = models.PositiveIntegerField(
        default=0, verbose_name="id для manufacturers"
    )
    atribute = models.ManyToManyField(Atribute, blank=True, verbose_name="Атрибуты")
    generic_atribute = models.BooleanField("Создать Атрибуты", default=False)
    stocks = models.BooleanField("Участвует в акции", default=False)
    order = models.BooleanField("Под заказ", default=False)
    review = models.BooleanField(
        default=True, blank=True, null=True, verbose_name="Отзывы"
    )
    reklama = models.BooleanField(
        default=True, blank=True, null=True, verbose_name="Рекламировать"
    )
    faqs = models.BooleanField(
        default=True, blank=True, null=True, verbose_name="Часто задаваемые вопросы"
    )
    comment = models.BooleanField(
        default=True, blank=True, null=True, verbose_name="Комментарии"
    )
    create = models.DateTimeField(auto_now=True, blank=True, null=True)
    site = models.ManyToManyField(Site, verbose_name="Сайты")
    weight = models.PositiveIntegerField(
        default=0, verbose_name="Вес", blank=True, null=True
    )
    width = models.PositiveIntegerField(
        default=0, verbose_name="Ширина", blank=True, null=True
    )
    height = models.PositiveIntegerField(
        default=0, verbose_name="Высота", blank=True, null=True
    )
    length = models.PositiveIntegerField(
        default=0, verbose_name="Длинна", blank=True, null=True
    )
    #
    # Габариты

    class Meta:
        db_table = "product"
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        ordering = ['position']

    def __str__(self):
        # Ensure that all components are convertible to strings
        return f'{self.name or "No Name"} - В наличии: {self.quantity}'

    def get_absolute_url(self):
        return reverse("shop:products", kwargs={"slug": self.slug})

    def get_review_rating(self):
        if self.review_count > 0:
            return self.review_all_sum / self.review_count
        return 0

    @property
    def has_default_image(self):
        return self.image.name == "default/product-nophoto.png"

    def generate_unique_article(self):
        """Генерирует уникальный артикул, состоящий только из цифр."""
        while True:
            article = ''.join(random.choices(string.digits, k=16))
            if not Products.objects.filter(article=article).exists():
                return article

    def get_final_price(self):
        if self.price_item and self.price_item.discount > 0:
            discount = self.price_item.discount
            return self.price * (1 - discount / 100)
        return self.price

    def generate_unique_article(self) -> str:
        """Сгенерировать уникальный артикул (пример)."""
        import uuid
        base = (self.slug or str(uuid.uuid4()))[:12].upper().replace("-", "")
        candidate = f"SKU-{base}"
        i = 1
        Model = type(self)
        while Model.objects.filter(article=candidate).exclude(pk=self.pk).exists():
            candidate = f"SKU-{base}-{i}"
            i += 1
        return candidate

    def _build_qr_content(self) -> str:
        # что кодируем (например, абсолютный URL товара)
        from django.contrib.sites.models import Site
        from django.urls import reverse
        domain = Site.objects.get_current().domain
        scheme = "https"
        url = reverse("shop:products", kwargs={"slug": self.slug})
        return f"{scheme}://{domain}{url}"

    def _make_qr_png(self) -> bytes:
        qr = qrcode.QRCode(
            version=None, error_correction=ERROR_CORRECT_M,
            box_size=8, border=2,
        )
        qr.add_data(self._build_qr_content())
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

        # --- единый save ---

    @classmethod
    def get_shop_category_products(cls, product, limit=8):
        """
        Получить 8 товаров из той же категории или родительских категорий
        """
        # Если у товара нет категорий, возвращаем пустой queryset
        if not product.category.exists():
            return cls.objects.none()

        # Получаем все категории товара
        product_categories = product.category.all()

        # Собираем все связанные категории
        all_related_categories = set()

        for category in product_categories:
            all_related_categories.update(category.get_related_categories())

        # Получаем товары из связанных категорий
        related_products = (
            cls.objects.filter(category__in=all_related_categories)
            .exclude(id=product.id)  # Исключаем текущий товар
            .distinct()
            .order_by('?')  # Случайный порядок
        )

        # Если не набрали достаточно товаров, дополняем любыми товарами
        if related_products.count() < limit:
            remaining = limit - related_products.count()
            additional_products = (
                cls.objects.exclude(id=product.id)
                .exclude(id__in=related_products.values_list('id', flat=True))
                .order_by('?')[:remaining]
            )
            return list(related_products) + list(additional_products)

        return related_products[:limit]

    @classmethod
    def get_products_from_category_or_above(cls, product, limit=8):
        """
        Получить любые 8 товаров из категории товара или выше (включая родительские),
        если товаров меньше, дополняем случайными товарами.
        """
        # Получаем все связанные категории (включая родительские)
        categories = product.category.all()
        related_categories = set()

        for category in categories:
            related_categories.update(category.get_related_categories())

        # Получаем товары из этих категорий, исключая текущий товар
        queryset = (
            cls.objects.filter(category__in=related_categories)
            .exclude(id=product.id)
            .distinct()
        )

        count = queryset.count()
        if count >= limit:
            return queryset[:limit]
        else:
            # Недостаточно товаров, дополняем случайными
            remaining = limit - count
            additional_products = (
                cls.objects.exclude(id=product.id)
                .exclude(id__in=queryset.values_list('id', flat=True))
                .order_by('?')[:remaining]
            )
            return list(queryset) + list(additional_products)


    def save(self, *args, **kwargs):
        creating = self._state.adding

        # 1) артикул до первого сохранения
        if not self.article:
            self.article = self.generate_unique_article()

        # (опц.) хотим узнавать, менялся ли slug
        old_slug = None
        if not creating and self.pk:
            old_slug = type(self).objects.filter(pk=self.pk).values_list("slug", flat=True).first()

        # 2) обычное сохранение (нужны pk/slug)
        super().save(*args, **kwargs)

        # 3) генерим/обновляем QR
        need_qr = False
        if creating and self.slug and not self.qr_code:
            need_qr = True
        elif old_slug is not None and old_slug != self.slug:
            # если надо обновлять QR при смене slug — оставь True
            need_qr = True

        if need_qr:
            png = self._make_qr_png()
            filename = f"product-{self.pk}.png"
            self.qr_code.save(filename, ContentFile(png), save=False)
            super().save(update_fields=["qr_code"])

    def _make_qr_image(self):
        pass


class CompareList(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="compare_lists"
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = (
            ("user", "site"),
            ("session_key", "site"),
        )

    def __str__(self):
        who = self.user or self.session_key or "unknown"
        return f"CompareList({who} @ {self.site_id})"

class CompareItem(models.Model):
    compare = models.ForeignKey(CompareList, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name="+")
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = (("compare", "product"),)


class FaqsProducts(models.Model):
    """Вопрос"""

    product = models.ForeignKey(
        Products,
        on_delete=models.CASCADE,
        related_name="product_faq",
        verbose_name="Образец Продукта",
        null=False,
        blank=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Пользователь",
    )
    question = models.TextField(blank=True, null=True, verbose_name="Вопрос")
    answer = models.TextField(blank=True, null=True, verbose_name="Ответ", default=" ")
    create = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    update = models.DateTimeField(auto_now=True, blank=True, null=True)
    publishet = models.BooleanField("Опубликован", default=True)

    def __str__(self):
        return f"{self.user} В наличии - {self.question}"

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"


class ProductsVariable(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=500, blank=True, null=True, verbose_name="URL")
    attribute = models.ManyToManyField(
        "Atribute",
        blank=True,
        verbose_name="Атрибуты",
        related_name="product_variables",
    )
    products = models.ForeignKey(
        "Products", on_delete=models.CASCADE, verbose_name="Образец Продукта"
    )
    site = models.ManyToManyField(Site, verbose_name="Сайты")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Количество")
    defaultposition = models.BooleanField(
        default=False, blank=True, null=True, verbose_name="Позиция по умолчанию"
    )
    price = models.DecimalField(
        max_digits=11, decimal_places=2, default=0.00, verbose_name="Цена"
    )
    price_item = models.ForeignKey(
        to=ProductsPrice,
        on_delete=models.CASCADE,
        verbose_name="Цена товара",
        blank=True,
        null=True,
    )
    costprice = models.DecimalField(
        max_digits=11,
        decimal_places=2,
        default=0.00,
        verbose_name="Цена себестоимости",
        blank=True,
        null=True,
    )
    costprice_item = models.ForeignKey(
        to=CostPrice,
        on_delete=models.CASCADE,
        verbose_name="Цена себестоимости",
        blank=True,
        null=True,
    )
    valute = models.ForeignKey(
        to=Valute,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Валюта",
    )
    image = models.FileField(
        "Изображение",
        upload_to=product_image_path,
        blank=True,
        null=True,
        default="default/product-nophoto.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    name = models.CharField(
        max_length=500,
        help_text="ссылка по которой будет доступен",
        verbose_name="Название",
    )
    weight = models.PositiveIntegerField(
        default=0, verbose_name="Вес", blank=True, null=True
    )
    width = models.PositiveIntegerField(
        default=0, verbose_name="Ширина", blank=True, null=True
    )
    height = models.PositiveIntegerField(
        default=0, verbose_name="Высота", blank=True, null=True
    )
    length = models.PositiveIntegerField(
        default=0, verbose_name="Длинна", blank=True, null=True
    )
    previev = models.FileField(
        upload_to="blogs/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Превью",
        default="default/imagegallery/imagegellery_images.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    title = models.CharField(
        max_length=150, verbose_name="Мета-заголовок", blank=True, null=True
    )
    metadescription = models.TextField(
        blank=True, null=True, verbose_name="Мета-описание"
    )
    propertytitle = models.CharField(
        verbose_name="Мета-заголовок ссылки",
        max_length=150,
        blank=True,
        null=True,
    )
    propertydescription = models.CharField(
        verbose_name="Мета-описание ссылки",
        max_length=255,
        blank=True,
        null=True,
    )
    create = models.DateTimeField(auto_now=True, blank=True, null=True)


    class Meta:
        verbose_name = "Вариация продукта"
        verbose_name_plural = "Вариации продуктов"
        ordering = ("create",)

class Reviews(models.Model):
    """Отзыв"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    publishet = models.BooleanField("Опубликован", default=True)
    text = models.TextField("комментарий")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Автор",
        on_delete=models.CASCADE, related_name="author",
    )
    product = models.ForeignKey(
        "Products", verbose_name="Продукт",
        on_delete=models.CASCADE, blank=True, null=True, related_name="reviews",
    )
    starvalue = models.PositiveIntegerField("Оценка в звездах", blank=True, default=1, null=True)
    create = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"


class ReviewImage(models.Model):
    review = models.ForeignKey(
        Reviews, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="reviews/images/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for review {self.review_id}"



class Complaint(models.Model):
    """Жалобы"""

    TYPE = [(1, "Подана"), (2, "Расматривается"), (3, "Урегулирован"), (4, "Отказан")]
    type = models.PositiveSmallIntegerField("Тип", choices=TYPE, blank=False, default=1)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(
        Chat, verbose_name="Чаты", on_delete=models.CASCADE, blank=True, null=True
    )
    products = models.ForeignKey(
        "Products",
        verbose_name="Товар",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    advertisement = models.ForeignKey(
        ProductsVariable,
        verbose_name="Вариация",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Авторы",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    create = models.DateTimeField(auto_now=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Жалоба"
        verbose_name_plural = "Жалобы"


"""Корзина"""


class SelectedProduct(models.Model):
    STATUS = [
        (1, "В корзине"),
        (2, "Оплачен"),
    ]
    reviews = models.BooleanField("Оставлен отзыв", default=False)
    status = models.PositiveIntegerField(
        "Статус продукта", choices=STATUS, blank=False, default=1
    )
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    product = models.ForeignKey(
        Products, on_delete=models.CASCADE, verbose_name="Товар"
    )
    review = models.ForeignKey(
        Reviews, on_delete=models.CASCADE, verbose_name="Отзыв", null=True, blank=True
    )
    quantity = models.PositiveIntegerField(default=0, verbose_name="Количество")
    session_key = models.CharField(max_length=32, null=True, blank=True)
    created_timestamp = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата добавления"
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Сумма"
    )
    variety = models.ForeignKey(
        ProductsVariable,
        on_delete=models.CASCADE,
        verbose_name="Вариация",
        blank=True,
        null=True,
    )
    create = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    update = models.DateTimeField(auto_now=True, blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Пользователь",
    )

    def __str__(self):
        return self.product.name

    class Meta:
        db_table = "selectedproduct"
        verbose_name = "Выбранный продукт"
        verbose_name_plural = "Выбранные продукты"
        ordering = ("id",)

    def calculate_amount(self):
        if self.variety:
            return self.quantity * self.variety.price
        else:
            if self.product and hasattr(self.product, "price"):
                return self.quantity * self.product.price
        return 0


class ProductComment(models.Model):
    STATUS_CHOICES = [
        (0, "Заказчик"),
        (1, "Поддержка"),
    ]
    status = models.SmallIntegerField(
        verbose_name="Статус", choices=STATUS_CHOICES, default=1, editable=False
    )
    ticket = models.ForeignKey(
        SelectedProduct,
        on_delete=models.CASCADE,
        verbose_name="Ticket",
        related_name="comments",
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    content = models.TextField(verbose_name="Комментарий")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        blank=True,
        null=True,
    )
    create = models.DateTimeField(auto_now=True, blank=True, null=True)
    publishet = models.BooleanField("Опубликован", default=True)

    class Meta:
        verbose_name = "Комментарий тикета"
        verbose_name_plural = "Комментарии тикета"
        ordering = ["-date"]


class ProductCommentMedia(models.Model):
    comment = models.ForeignKey(
        "ProductComment", on_delete=models.CASCADE, related_name="commentmedia"
    )
    file = models.FileField(upload_to="ticket/%Y/%m/%d/tiket_file/")

    def get_file_name(self):
        return os.path.basename(self.file.name)

    class Meta:
        verbose_name = "Файл комментария тикета"
        verbose_name_plural = "Файлы комментариев тикета"


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Пользователь",
    )
    gabarite = models.TextField("Габариты")
    selectedproduct = models.ManyToManyField(
        to="SelectedProduct", verbose_name="Выбранные Товары", blank=True
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Сумма"
    )
    convert_valute = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Сумма в валюте корзины"
    )
    session_key = models.CharField(max_length=32, null=True, blank=True)
    browser_key = models.CharField(max_length=32, null=True, blank=True)
    valute = models.ForeignKey(
        to=Valute,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Валюта",
    )
    site = models.ForeignKey(
        Site, on_delete=models.CASCADE, verbose_name="Сайт"
    )  # Только один сайт на корзину

    class Meta:
        db_table = "cart"
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"
        unique_together = [
            ("user", "site"),
            ("browser_key", "site"),
        ]

    def get_cart_owner(self):
        if self.user:
            return self.user.username
        return self.session_key

    def get_products_count(self):
        """
        Возвращает количество выбранных товаров в корзине
        """
        return self.selectedproduct.count()

    def __str__(self):
        if self.user:
            return f"Корзина {self.user.username} | Сумма {self.amount}"
        return f"Анонимная корзина | Сумма {self.amount}"

    def update_amount(self):
        total = Decimal("0.00")
        for sp in self.selectedproduct.all():
            if sp.variety and sp.variety.price is not None:
                item_price = sp.variety.price
            elif hasattr(sp.product, "price") and sp.product.price is not None:
                item_price = sp.product.price
            else:
                item_price = Decimal("0.00")

            new_amount = item_price * sp.quantity

            # Выведем для отладки
            print(
                f"SelectedProduct {sp.id}: price={item_price}, quantity={sp.quantity}, new_amount={new_amount}, old_amount={sp.amount}"
            )

            if sp.amount != new_amount:
                sp.amount = new_amount
                sp.save(update_fields=["amount"])

            total += new_amount

        print(f"Total calculated: {total}, old cart amount: {self.amount}")
        if self.amount != total:
            self.amount = total
            self.save(update_fields=["amount"])
            print(f"Cart amount updated to {self.amount}")
        else:
            print("Cart amount not changed")

    def save(self, *args, **kwargs):
        if not self.valute:
            self.valute = Valute.objects.filter(default=True).first()
        super(Cart, self).save(*args, **kwargs)

    def get_cart_total(self):
        """
        Возвращает общую сумму корзины с учетом валюты
        """
        total = sum(item.amount for item in self.selectedproduct.all())
        return f"{total:.2f} {self.valute.icon_code}" if self.valute else f"{total:.2f}"

    def get_total(self):
        return sum(item.amount for item in self.selectedproduct.all())

    def get_formatted_total(self):
        return f"{self.get_total():.2f} ₽"


class Storage(models.Model):
    """Страницы"""

    name = models.CharField("Название", help_text="Название", max_length=550)
    address = models.CharField("Адрес", max_length=550)
    city = models.CharField("Город", max_length=550)
    zip_index = models.CharField("Почтовый индекс", max_length=550)
    longitude = models.TextField("Долгота", max_length=550)
    latitude = models.TextField("Широта", max_length=550)
    content = models.TextField(blank=True, null=True, verbose_name="Описание")
    email = models.TextField(blank=True, null=True, verbose_name="Контактная почта ")
    contact_name = models.TextField(
        blank=True, null=True, verbose_name="Контактный Имя"
    )
    contact_phone = models.TextField(
        blank=True, null=True, verbose_name="Контактный номер"
    )
    delivery_comment = models.TextField(
        blank=True, null=True, verbose_name="Комментарий склада для доставки"
    )

    def __str__(self):
        return f"Номер -{self.id} адрес - {self.address}"

    class Meta:
        verbose_name = "Склад"
        verbose_name_plural = "Склады"


class StockAvailability(models.Model):
    """Изображения продуктов"""

    create = models.DateTimeField(auto_now=True, blank=True, null=True)
    products = models.ForeignKey(
        Products, on_delete=models.CASCADE, verbose_name="Образец Продукта"
    )
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, verbose_name="Склад")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Количество")

    def __str__(self):
        return f"{self.products} Количество - {self.quantity}"

    class Meta:
        verbose_name = "Наличие на складе"
        verbose_name_plural = "Наличия на складах"




class ImportHistory(models.Model):
    # Поля для хранения файла или ссылки
    file = models.FileField(upload_to='imports/%Y/%m/%d/', verbose_name="Файл для импорта", null=True, blank=True)
    file_url = models.URLField(verbose_name="Ссылка на файл", null=True, blank=True)
    shop_id = models.CharField(max_length=10, verbose_name="Shop_id")
    # Тип файла (например, CSV, XML, XLS)
    file_type = models.CharField(max_length=10, choices=[('csv', 'CSV'), ('xls', 'XLSX'), ('xml', 'XML')],
                                 verbose_name="Тип файла")
    language = models.CharField(
        max_length=5,
        choices=settings.LANGUAGES,
        default='en',
        verbose_name="Язык",
        help_text="Выберите язык импорта",
    )

    # Статус импорта
    status = models.CharField(max_length=20, choices=[('pending', 'В ожидании'), ('in_progress', 'В процессе'),
                                                      ('completed', 'Завершен'), ('failed', 'Ошибка')],
                              default='pending', verbose_name="Статус")

    # Время создания и обновления
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    # Время начала и завершения импорта
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата начала импорта")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата завершения импорта")

    # Пользователь, который инициирует импорт
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь",
                             blank=True, null=True)

    # Поля для расписания
    scheduled_time = models.DateTimeField(default=timezone.now, verbose_name="Запланированное время", null=True,
                                          blank=True)
    schedule_type = models.CharField(max_length=20, choices=[
        ('daily', 'Каждый день'),
        ('weekly', 'По дням недели'),
        ('custom_dates', 'По выбранным датам')
    ], default='daily', verbose_name="Тип расписания")

    daily_time = models.TimeField(null=True, blank=True, verbose_name="Время для ежедневного импорта")
    days_of_week = models.CharField(max_length=100, blank=True, null=True,
                                    help_text="Список дней недели через запятую (например, 'Monday, Wednesday')")

    custom_dates = models.TextField(null=True, blank=True,
                                    help_text="Список дат для импорта в формате YYYY-MM-DD, через запятую.")
    valute = models.ForeignKey(
        to=Valute,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Валюта",
    )

    def __str__(self):
        return f"Import {self.id} - {self.file.name if self.file else self.file_url}"

    class Meta:
        verbose_name = "Лог импорта"
        verbose_name_plural = "Логи импорта"
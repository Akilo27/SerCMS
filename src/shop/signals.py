from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from .models import (
    SelectedProduct,
    Reviews,
    Products,
    Categories,
    Manufacturers,
    ProductsVariable,
    StockAvailability,Atribute,
    Storage, Cart, Valute,Variable
)
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.text import slugify
from django.db.models.signals import pre_save
import re
from payment.models import Order
from decimal import Decimal, ROUND_DOWN
import json
from django.contrib.sites.models import Site
from webmain.models import SettingsGlobale
import itertools
# app/signals.py
from .models import ProductsPrice, CostPrice
import secrets
from itertools import product

from django.db import transaction, IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.sites.models import Site
from .models import Products, ProductsVariable, Variable

from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist



# @receiver(post_save, sender=Products)
# def ensure_qr(sender, instance: Products, created, **kwargs):
#     if (created or not instance.qr_code) and instance.slug:
#         png = instance._make_qr_image()
#         instance.qr_code.save(f"product-{instance.pk}.png", ContentFile(png), save=False)
#         instance.save(update_fields=["qr_code"])


# @receiver(post_save, sender=Products)
# def create_price_objects(sender, instance, created, **kwargs):
#     if hasattr(instance, "_price_signal_done"):
#         return  # сигнал уже обработан, выходим
#
#     # Устанавливаем флаг, чтобы при повторном save сигнал не сработал
#     instance._price_signal_done = True
#
#     if created or instance.price_item is None:
#         new_price = ProductsPrice.objects.create(
#             product=instance, price=instance.price, wholesale_price=0.00, discount=0.00
#         )
#         instance.price_item = new_price
#
#     if created or instance.costprice_item is None:
#         new_costprice = CostPrice.objects.create(
#             product=instance,
#             price=instance.costprice,
#             wholesale_price=0.00,
#             discount=0.00,
#         )
#         instance.costprice_item = new_costprice
#
#     # Сохраняем объект с новыми связями
#     instance.save(update_fields=["price_item", "costprice_item"])

@receiver(post_save, sender=Manufacturers)
def generate_manufacturer_token(sender, instance, created, **kwargs):
    # Генерируем токен только если он еще не существует
    if created and not instance.token:
        token = secrets.token_urlsafe(64)  # Генерация безопасного токена
        instance.token = token
        instance.save()
        print(f"Токен для магазина {instance.shop_id} сгенерирован: {token}")


@receiver(post_save, sender=SelectedProduct)
@receiver(post_delete, sender=SelectedProduct)
def update_cart_gabarite(sender, instance, **kwargs):
    """
    Сигнал, который обновляет поле gabarite в корзине Cart при добавлении или удалении товара в SelectedProduct.
    """
    # Получаем все корзины, содержащие данный товар
    carts = Cart.objects.filter(selectedproduct=instance)

    # Проходим по всем корзинам, содержащим этот товар
    for cart in carts:
        # Собираем габариты всех товаров в корзине
        selected_products = cart.selectedproduct.all()
        gabarites = []

        for selected_product in selected_products:
            product = selected_product.product
            gabarite = {
                "product_id": str(product.id),  # Преобразуем UUID в строку
                "product_name": product.name,  # Используем правильное имя продукта
                "quantity": selected_product.quantity,
                "weight": product.weight,
                "length": product.length,
                "width": product.width,
                "height": product.height
            }
            gabarites.append(gabarite)

        # Обновляем поле gabarite в корзине
        cart.gabarite = json.dumps(gabarites, ensure_ascii=False)  # Используем ensure_ascii=False
        cart.save()



@receiver(post_save, sender=Reviews)
def update_order_reviews(sender, instance, created, **kwargs):
    if created:
        product = instance.product
        product.review_count += 1
        product.review_all_sum += instance.starvalue
        product.review_rating = product.review_all_sum // product.review_count
        product.save()

        orders = Order.objects.filter(selectedproduct__product=product)

        for order in orders:
            order.reviews = True
            order.save()


@receiver(post_save, sender=SelectedProduct)
def selected_product_saved(sender, instance, **kwargs):
    if instance.cart_set.exists():
        for cart in instance.cart_set.all():
            cart.update_amount()


@receiver(post_delete, sender=SelectedProduct)
def selected_product_deleted(sender, instance, **kwargs):
    if instance.cart_set.exists():
        for cart in instance.cart_set.all():
            cart.update_amount()


@receiver(pre_delete, sender=SelectedProduct)
def selected_product_pre_delete(sender, instance, **kwargs):
    # Получаем все корзины, где используется этот SelectedProduct
    carts = instance.cart_set.all()
    for cart in carts:
        if cart.amount is None:
            cart.amount = Decimal("0.00")

        # Уменьшаем сумму корзины на amount удаляемого продукта
        cart.amount -= instance.amount or Decimal("0.00")
        if cart.amount < 0:
            cart.amount = Decimal("0.00")  # Без отрицательных сумм

        cart.save(update_fields=["amount"])


@receiver(post_save, sender=SelectedProduct)
def selected_product_post_save(sender, instance, created, **kwargs):
    # При сохранении пересчитываем сумму корзины (например, при изменении количества или цены)
    carts = instance.cart_set.all()
    for cart in carts:
        cart.update_amount()


@receiver(post_save, sender=Products)
def ensure_stock_availability(sender, instance, created, **kwargs):
    if created:
        try:
            # Используйте транзакции для безопасного создания объектов
            with transaction.atomic():
                # Проверьте, если `StockAvailability` уже существует
                if not StockAvailability.objects.filter(products=instance).exists():
                    storage = Storage.objects.first()
                    if storage:
                        StockAvailability.objects.create(
                            products=instance,
                            storage=storage,
                            quantity=instance.quantity,
                        )
        except IntegrityError as e:
            # Обработка ошибки при создании объектов
            print(f"Error creating StockAvailability for {instance}: {e}")
    try:
        settingsglobale = SettingsGlobale.objects.get(site=instance.site.first())
        if instance.price > settingsglobale.max_price_product:
            settingsglobale.max_price_product = instance.price
            settingsglobale.save()
    except:
        pass


# Словарь для замены кириллических букв на латинские
CYRILLIC_TO_LATIN = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ы": "y",
    "э": "e",
    "ю": "yu",
    "я": "ya",
    "ъ": "",
    "ь": "",
}

CYRILLIC_TO_LATIN = {
    # Пример соответствия кириллических букв латинским
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "yo",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def transliterate(text):
    text = text.lower()  # Приведение к нижнему регистру
    transliterated_text = "".join(CYRILLIC_TO_LATIN.get(char, char) for char in text)

    # Удаление недопустимых символов, кроме букв, цифр, тире и подчеркивания
    cleaned_text = re.sub(r"[^a-z0-9_-]", "-", transliterated_text)

    # Замена множественных тире на одно
    cleaned_text = re.sub(r"-+", "-", cleaned_text)

    # Удаление тире в начале и конце строки
    cleaned_text = cleaned_text.strip("-")

    return cleaned_text


def generate_unique_slug(model, slug):
    original_slug = slug
    queryset = model.objects.filter(slug=slug).exists()
    count = 1

    while queryset:
        slug = f"{original_slug}-{count}"
        queryset = model.objects.filter(slug=slug).exists()
        count += 1

    return slug


@receiver(pre_save, sender=Categories)
def generate_category_slug(sender, instance, **kwargs):
    if not instance.slug:
        # Преобразуем кириллические буквы в латинские и заменяем пробелы на тире
        latin_text = transliterate(instance.name)
        # Используем slugify для приведения к корректному slug
        slug = slugify(latin_text)
        # Генерируем уникальный слаг
        instance.slug = generate_unique_slug(Categories, slug)


@receiver(pre_save, sender=Categories)
def generate_categories_slug(sender, instance, **kwargs):
    if not instance.slug:
        # Преобразуем кириллические буквы в латинские и заменяем пробелы на тире
        latin_text = transliterate(instance.name)
        # Используем slugify для приведения к корректному slug
        slug = slugify(latin_text)
        # Генерируем уникальный слаг
        instance.slug = generate_unique_slug(Categories, slug)


@receiver(pre_save, sender=Products)
def generate_product_slug(sender, instance, **kwargs):
    if not instance.slug:  # Если slug не установлен, генерируем его
        latin_text = transliterate(instance.name)
        slug = latin_text
        # Генерируем уникальный слаг
        instance.slug = generate_unique_slug(Products, slug)


@receiver(pre_save, sender=Manufacturers)
def generate_manufacturers_slug(sender, instance, **kwargs):
    if not instance.slug:  # Если slug не установлен, генерируем его
        latin_text = transliterate(instance.name)
        slug = latin_text
        # Генерируем уникальный слаг
        instance.slug = generate_unique_slug(Manufacturers, slug)


@receiver(pre_save, sender=SelectedProduct)
def update_amount(sender, instance, **kwargs):
    """
    Сигнал для обновления поля `amount` при изменении `quantity`.
    """
    print("yes")
    if instance.variety:
        instance.amount = instance.quantity * instance.variety.price
    elif instance.product:
        instance.amount = instance.quantity * instance.product.price
    else:
        instance.amount = 0


# @receiver(pre_save, sender=ProductsVariable)
# def update_product_price(sender, instance, **kwargs):
#     first_variable = (
#         ProductsVariable.objects.filter(products=instance.products)
#         .order_by("id")
#         .first()
#     )
#
#     # Если найден первый связанный экземпляр, обновляем цену продукта
#     if first_variable and instance.products.price != first_variable.price:
#         instance.products.price = first_variable.price
#         instance.products.save()


@receiver(pre_save, sender=Cart)
def update_convert_valute_on_valute_change(sender, instance, **kwargs):
    if not instance.amount or not instance.valute:
        instance.convert_valute = 0
        return

    try:
        base_valute = Valute.objects.filter(default=True).first()
        if not base_valute or not base_valute.relationship:
            # Нет базовой валюты — просто копируем amount
            instance.convert_valute = instance.amount
            return

        # Если валюта корзины = дефолтная — не конвертируем
        if instance.valute == base_valute:
            instance.convert_valute = instance.amount
            return

        amount = Decimal(instance.amount)
        rel = Decimal(instance.valute.relationship)

        # 🔁 Конвертация по знаку relationship
        if rel < 0:
            converted = amount / abs(rel)
        else:
            converted = amount * rel

        # 💰 Наценка (если есть)
        allowance = Decimal(instance.valute.allowance or 0)
        if allowance != 0:
            converted += converted * (allowance / Decimal(100))

        # Округление
        converted = converted.quantize(Decimal("1.00"), rounding=ROUND_DOWN)
        instance.convert_valute = converted

    except Exception as e:
        print(f"[update_convert_valute_on_valute_change] Error: {e}")
        instance.convert_valute = instance.amount  # fallback


import itertools
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Products, Atribute, ProductsVariable
import uuid

def create_product_variations(instance):
    """
    Создает вариации продукта с комбинациями атрибутов
    """
    print(f"Обработка продукта: {instance.name} (ID: {instance.id})")
    print(f"Исходная цена: {instance.price}")
    print(f"Количество: {instance.quantity}")

    # Удаляем старые вариации перед созданием новых
    ProductsVariable.objects.filter(products=instance).delete()
    print("Старые вариации удалены")

    # Получаем активные атрибуты (с ценой > 0)
    active_attributes = instance.atribute.filter(variable__price__gt=0).select_related('variable')
    attribute_names = []
    attribute_prices = []

    for attr in active_attributes:
        if attr.variable.name not in attribute_names:
            attribute_names.append(attr.variable.name)
            attribute_prices.append(attr.variable.price)

    print(f"Активные атрибуты: {attribute_names}")
    print(f"Цены атрибутов: {attribute_prices}")

    # Создаем базовую вариацию (без атрибутов)
    base_variation = ProductsVariable(
        products=instance,
        price=instance.price,  # Используем исходную цену продукта
        quantity=instance.quantity,
        name=instance.name,
        defaultposition=True,
        slug=str(uuid.uuid4()),
    )
    base_variation.save()
    print(f"Создана базовая вариация с ценой {instance.price}")

    # Присваиваем сайт через ManyToMany
    base_variation.site.set(instance.site.all())  # Если `site` это ManyToManyField
    base_variation.save()

    # Генерируем все комбинации атрибутов (0 - неактивен, 1 - активен)
    combinations = itertools.product([0, 1], repeat=len(attribute_names))

    # Пропускаем первую комбинацию (все нули) - это базовая вариация
    next(combinations)

    for combination in combinations:
        # Вычисляем цену для комбинации
        price = instance.price
        active_attrs_for_combination = []

        for i, is_active in enumerate(combination):
            if is_active:
                price += attribute_prices[i]
                active_attrs_for_combination.append(active_attributes[i])

        # Создаем вариацию
        variation = ProductsVariable(
            products=instance,
            price=price,
            quantity=instance.quantity,
            name=instance.name,
            defaultposition=False,
            slug=str(uuid.uuid4()),
        )
        variation.save()

        # Присваиваем сайт для вариации через ManyToMany
        variation.site.set(instance.site.all())  # Если `site` это ManyToManyField
        variation.save()

        # Добавляем атрибуты
        for attr in active_attrs_for_combination:
            variation.attribute.add(attr)

        print(f"Создана вариация с атрибутами {combination}, цена: {price}")

    print(f"Завершено создание вариаций для продукта {instance.name}\n")


@receiver(post_save, sender=Products)
def handle_product_variations(sender, instance, created, **kwargs):
    """
    Обработчик сигнала для создания вариаций продукта
    """
    # Пропускаем новые продукты и продукты без флага generic_atribute
    if created or not instance.generic_atribute:
        return

    # Проверяем, не выполняется ли уже обработка для этого продукта
    if hasattr(instance, '_creating_variations'):
        return

    # Помечаем продукт как обрабатываемый
    instance._creating_variations = True

    try:
        # Используем транзакцию и отложенное выполнение
        transaction.on_commit(lambda: create_product_variations(instance))
    finally:
        # Снимаем метку после завершения
        delattr(instance, '_creating_variations')

@receiver(post_save, sender=ProductsVariable)
def update_product_variable_json(sender, instance, created, **kwargs):
    # Получаем продукт, к которому привязана данная переменная
    product = instance.products

    # Получаем все переменные, связанные с данным продуктом
    product_variables = ProductsVariable.objects.filter(products=product)

    # Формируем новый список данных для variable_json
    variable_data = []
    for variable in product_variables:
        # Перечисляем атрибуты через запятую
        attributes = ", ".join([str(attr.id) for attr in variable.attribute.all()])

        variable_data.append({
            "slug": variable.slug,
            "price": str(variable.price),
            "quantity": variable.quantity,
            "attributes": attributes  # Атрибуты через запятую
        })

    # Обновляем поле variable_json в модели Products
    product.variable_json = json.dumps(variable_data)

    # Сохраняем изменения в продукте
    product.save()



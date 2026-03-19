import os
import sys
import django
import uuid
import requests
import json
from io import BytesIO
from django.core.files import File
from django.utils.text import slugify
from googletrans import Translator  # pip install googletrans==4.0.0-rc1

# --- Django setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_project.settings")
django.setup()

from shop.models import (
    Products,
    ProductsPrice,
    ProductsVariable,
    Manufacturers,
    Site,
    Valute,
    Categories,
    Variable,
    Atribute,
    ProductsGallery,
)

# ====== Переводчик ======
translator = Translator()

def translate_text(text, lang):
    """Перевод текста через Google Translate"""
    if not text:
        return ""
    try:
        result = translator.translate(text, src="ru", dest=lang)
        return result.text
    except Exception as e:
        print(f"Ошибка перевода [{lang}]: {e}")
        return text


# ====== Вспомогательные ======
def generate_unique_slug(name: str) -> str:
    """Генерируем уникальный slug для Products"""
    base_slug = slugify(name)[:180] or f"product-{uuid.uuid4().hex[:6]}"
    slug = base_slug
    counter = 1
    while Products.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug

def download_image(url):
    """Скачивание изображения из URL"""
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            filename = url.split("/")[-1]
            return File(BytesIO(resp.content), name=filename)
    except Exception as e:
        print(f"Ошибка загрузки {url}: {e}")
    return None

def get_or_create_category(cat_name, site):
    """Создать или найти категорию"""
    cat_obj, _ = Categories.objects.get_or_create(
        name=cat_name,
        parent=None,
        defaults={"slug": slugify(cat_name)[:200] or f"cat-{uuid.uuid4().hex[:6]}"},
    )
    cat_obj.site.add(site)
    return cat_obj

def get_or_create_attribute(name, value, site):
    """Создать Variable и Atribute"""
    slug_base = slugify(name) or f"var-{uuid.uuid4().hex[:6]}"
    variable = Variable.objects.filter(name=name).first()
    if not variable:
        slug = slug_base
        counter = 1
        while Variable.objects.filter(slug=slug).exists():
            slug = f"{slug_base}-{counter}"
            counter += 1

        variable = Variable.objects.create(
            name=name,
            slug=slug,
            type=2,
            variabletype=3,
        )
        variable.site.add(site)

    # Атрибут
    attr_slug = slugify(value) or f"attr-{uuid.uuid4().hex[:6]}"
    attr = Atribute.objects.filter(name=value, variable=variable).first()
    if not attr:
        counter = 1
        slug = attr_slug
        while Atribute.objects.filter(slug=slug).exists():
            slug = f"{attr_slug}-{counter}"
            counter += 1
        attr = Atribute.objects.create(
            name=value,
            variable=variable,
            slug=slug,
            content=value,
        )
    return attr


# ====== Основной импорт ======

json_file = "/_dump/nut/funduchok_products.json"
json_file = "/home/akilo/PycharmProjects/unicalCMS/src/_dump/nut/funduchok_products.json"

with open(json_file, "r", encoding="utf-8") as f:
    products_data = json.load(f)

# Настройки по умолчанию
default_site = Site.objects.filter(id=1).first()
default_valute = Valute.objects.filter(default=True).first()
default_manufacturer = Manufacturers.objects.first()

if not default_site or not default_valute:
    print("❌ Проверьте наличие сайта и валюты")
    sys.exit(1)

count_new = 0
count_exist = 0

for data in products_data:  # список товаров
    # Делаем article уникальным
    if data.get("id"):
        article = f"funduchok-{data['id']}"
    else:
        article = f"AUTO-{uuid.uuid4().hex[:8]}"

    product, created = Products.objects.get_or_create(
        article=article,
        defaults={
            "name": data.get("name", ""),
            "slug": generate_unique_slug(data.get("name", "")),
            "description": data.get("description_text", ""),
            "fragment": data.get("description_html", ""),
            "price": data.get("base_price", 0),
            "valute": default_valute,
            "quantity": 1000,
            "type": 3 if data.get("variants") else 1,
            "typeofchoice": 1,
        },
    )

    if not created:
        print(f"⏭ Пропущен (уже существует): {product.name} [{article}]")
        count_exist += 1
        continue

    product.site.add(default_site)
    if default_manufacturer:
        product.manufacturers.add(default_manufacturer)

    # Главное изображение
    if data.get("main_image"):
        main_image = download_image(data["main_image"])
        if main_image:
            product.image.save(main_image.name, main_image, save=True)

    # Категория
    if data.get("category"):
        cat = get_or_create_category(data["category"], default_site)
        product.category.add(cat)

    # Атрибуты из properties
    for key, val in data.get("properties", {}).items():
        attr = get_or_create_attribute(key, val, default_site)
        product.atribute.add(attr)

    # Галерея
    for g_url in data.get("gallery", []):
        g_file = download_image(g_url)
        if g_file:
            ProductsGallery.objects.create(products=product, image=g_file)

    # Цены / вариации
    if not data.get("variants"):  # обычный товар
        ProductsPrice.objects.create(product=product, price=data.get("base_price", 0))
    else:  # вариативный товар
        for var in data["variants"]:
            price = var.get("price", 0)
            name = var.get("title", "")

            price_obj = ProductsPrice.objects.create(product=product, price=price)

            var_obj = ProductsVariable.objects.create(
                products=product,
                slug=str(uuid.uuid4()),
                name=name[:200],
                price=price,
                price_item=price_obj,
                quantity=1000,
            )
            var_obj.site.add(default_site)

            if var.get("option_name") and var.get("weight_g"):
                attr = get_or_create_attribute(
                    var["option_name"], f"{var['weight_g']} г.", default_site
                )
                var_obj.attribute.add(attr)

            var_obj.save()

    # ===== Переводы через Google Translate =====
    product.name_en = translate_text(product.name, "en")
    product.name_tg = translate_text(product.name, "tg")
    product.name_tr = translate_text(product.name, "tr")
    product.name_kk = translate_text(product.name, "kk")
    product.name_uz = translate_text(product.name, "uz")

    product.description_en = translate_text(product.description, "en")
    product.description_tg = translate_text(product.description, "tg")
    product.description_tr = translate_text(product.description, "tr")
    product.description_kk = translate_text(product.description, "kk")
    product.description_uz = translate_text(product.description, "uz")

    product.fragment_en = translate_text(product.fragment, "en")
    product.fragment_tg = translate_text(product.fragment, "tg")
    product.fragment_tr = translate_text(product.fragment, "tr")
    product.fragment_kk = translate_text(product.fragment, "kk")
    product.fragment_uz = translate_text(product.fragment, "uz")

    product.save()

    count_new += 1
    print(f"✅ Новый импортирован: {product.name} [{article}]")

print(f"\n🎉 Импорт завершён. Новых товаров: {count_new}, уже существовало: {count_exist}")

import os
import sys
import django
import uuid
import pandas as pd
import requests
from io import BytesIO
from collections import defaultdict
from django.core.files import File
from django.utils.text import slugify
from django.db import transaction
from decimal import Decimal, InvalidOperation

# --- Django setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
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


# --- Вспомогательные функции ---

def parse_price(price_str):
    try:
        if price_str is None or (isinstance(price_str, float) and pd.isna(price_str)):
            return 0.0

        # Обрабатываем случаи с очень большими числами
        price_str = str(price_str).replace("₺", "").replace(",", ".").strip()

        # Проверяем, не является ли цена астрономически большой
        price_value = float(price_str)
        if price_value > 1000000000:  # Если больше 1 миллиарда
            print(f"⚠️  Подозрительно большая цена: {price_value}, устанавливаем 0")
            return 0.0

        return price_value
    except Exception as e:
        print(f"Ошибка парсинга цены: {price_str} — {e}")
        return 0.0


def extract_variant_key(code):
    if isinstance(code, str) and "mpn:" in code and "-" in code:
        start = code.find("mpn:") + 4
        end = code.find("-", start)
        return code[start:end].strip()
    return None


def get_or_create_categories_from_path(cat_path, site):
    categories = []
    parent = None
    for cat_name in cat_path.split(">"):
        cat_name = cat_name.strip()

        cat_obj = Categories.objects.filter(name=cat_name, parent=parent).first()
        if not cat_obj:
            cat_obj = Categories.objects.create(
                name=cat_name, slug=slugify(cat_name), parent=parent
            )
            cat_obj.site.add(site)
            cat_obj.save()

        parent = cat_obj
        categories.append(cat_obj)
    return categories


def create_size_variables(site):
    numeric_var, _ = Variable.objects.get_or_create(
        slug="size_numeric",
        defaults={"name": "Размеры (числовые)", "type": 3, "variabletype": 3},
    )
    letter_var, _ = Variable.objects.get_or_create(
        slug="size_letter",
        defaults={"name": "Размеры (буквенные)", "type": 2, "variabletype": 3},
    )
    numeric_var.site.add(site)
    letter_var.site.add(site)
    numeric_var.save()
    letter_var.save()

    numeric_attrs = {}
    for i in range(1, 51):
        attr, _ = Atribute.objects.get_or_create(
            slug=f"size_numeric_{i}", variable=numeric_var, defaults={"name": str(i)}
        )
        numeric_attrs[str(i)] = attr

    letter_sizes = ["S", "M", "L", "XL", "XXL"]
    letter_attrs = {}
    for size_name in letter_sizes:
        attr, _ = Atribute.objects.get_or_create(
            slug=f"size_letter_{size_name.lower()}",
            variable=letter_var,
            defaults={"name": size_name},
        )
        letter_attrs[size_name] = attr

    return numeric_attrs, letter_attrs


def find_size_attributes_for_value(size_value, numeric_attrs, letter_attrs):
    size_value_str = str(size_value).strip()
    if size_value_str in numeric_attrs:
        return numeric_attrs[size_value_str]
    size_value_up = size_value_str.upper()
    if size_value_up in letter_attrs:
        return letter_attrs[size_value_up]
    return None


def download_image_from_url(url):
    try:
        print(f"Downloading image from URL: {url}")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            filename = url.split("/")[-1].split("?")[0]
            print(f"Image downloaded successfully: {filename}")
            return File(BytesIO(response.content), name=filename)
        else:
            print(f"Failed to download image, status code: {response.status_code}")
    except Exception as e:
        print(f"Ошибка загрузки изображения: {url} — {e}")
    return None


def split_image_urls(images_field):
    parts = images_field.replace(",https://", "|https://").split("|")
    return [p.strip() for p in parts if p.strip()]


def get_or_create_product(name, manufacturer, site, valute, **kwargs):
    """Получить или создать продукт по имени и производителю"""
    try:
        product = Products.objects.filter(name=name).first()

        if product:
            print(f"🔄 Обновляем существующий продукт: {name}")
            # Обновляем поля
            for key, value in kwargs.items():
                if hasattr(product, key) and value is not None:
                    setattr(product, key, value)
            product.save()
            return product, True  # True - продукт существовал
        else:
            print(f"✅ Создаем новый продукт: {name}")
            # Сначала создаем продукт без manufacturers
            product_data = {
                'name': name,
                'valute': valute,
                **{k: v for k, v in kwargs.items() if k != 'manufacturers'}
            }
            product = Products.objects.create(**product_data)

            # Затем добавляем manufacturers через many-to-many
            product.manufacturers.add(manufacturer)
            product.site.add(site)

            return product, False  # False - продукт новый
    except Exception as e:
        print(f"❌ Ошибка при создании/обновлении продукта {name}: {e}")
        return None, False


def update_or_create_variation(product, variation_data, price_value, numeric_attrs, letter_attrs, default_site):
    """Обновить или создать вариацию продукта"""
    try:
        # Ищем вариацию по имени или создаем новую
        variation_name = variation_data.get("Наименование", "")[:500]
        variation_code = variation_data.get("product_code", "")

        variation = ProductsVariable.objects.filter(
            products=product,
            name=variation_name
        ).first()

        if variation:
            print(f"   🔄 Обновляем вариацию: {variation_name}")
            variation.price = price_value
            variation.quantity = 1000
            variation.save()
        else:
            print(f"   ✅ Создаем новую вариацию: {variation_name}")
            price_obj = ProductsPrice.objects.create(
                product=product,
                price=price_value,
            )

            variation = ProductsVariable.objects.create(
                slug=str(uuid.uuid4()),
                products=product,
                price=price_value,
                price_item=price_obj,
                quantity=1000,
                name=variation_name,
            )
            variation.site.add(default_site)

        # Обновляем атрибуты размеров
        sizes_str = variation_data.get("sizes", "")
        size_values = [
            s.strip()
            for s in str(sizes_str).replace(";", ",").split(",")
            if s.strip()
        ]

        # Очищаем старые атрибуты и добавляем новые
        variation.attribute.clear()
        for size_val in size_values:
            attr = find_size_attributes_for_value(size_val, numeric_attrs, letter_attrs)
            if attr:
                variation.attribute.add(attr)

        variation.save()
        return variation
    except Exception as e:
        print(f"❌ Ошибка при создании/обновлении вариации: {e}")
        return None


def update_product_gallery(product, image_urls):
    """Обновить галерею продукта"""
    try:
        # Удаляем старые изображения галереи (кроме основного)
        ProductsGallery.objects.filter(products=product).delete()

        # Добавляем новые изображения галереи (начиная со второго URL)
        gallery_images = image_urls[1:] if len(image_urls) > 1 else []

        for g_img_url in gallery_images:
            img_file = download_image_from_url(g_img_url)
            if img_file:
                ProductsGallery.objects.create(products=product, image=img_file)
                print(f"   ✅ Добавлено изображение в галерею: {g_img_url}")
            else:
                print(f"   ❌ Ошибка загрузки изображения галереи: {g_img_url}")
    except Exception as e:
        print(f"❌ Ошибка при обновлении галереи: {e}")


# --- Основной код ---

@transaction.atomic
def main():
    try:
        df = pd.read_excel(
            "/app/marketplace/_dump/20250914085748_sarvar@hozplanet_1382240427_2.xlsx")

        default_manufacturer = Manufacturers.objects.filter(id=1).first()
        default_site = Site.objects.filter(id=1).first()
        default_valute = Valute.objects.filter(default=True).first()

        if not default_manufacturer or not default_site or not default_valute:
            print("❌ Проверьте наличие производителей, сайтов и валют.")
            sys.exit(1)

        numeric_attrs, letter_attrs = create_size_variables(default_site)

        # Группируем по ключу вариантов
        variant_groups = defaultdict(list)
        for _, row in df.iterrows():
            code = row.get("product_code", "")
            key = extract_variant_key(code) or uuid.uuid4().hex
            variant_groups[key].append(row)

        total_updated = 0
        total_created = 0
        total_errors = 0

        for key, group in variant_groups.items():
            try:
                base_data = group[0]

                images_field = str(base_data.get("images", ""))
                image_urls = split_image_urls(images_field)

                # Загружаем основное изображение
                main_image = download_image_from_url(image_urls[0]) if image_urls else None

                # Получаем или создаем продукт
                posted =  base_data["Архивный"] == "нет"
                product, existed = get_or_create_product(
                    name=base_data["Наименование"],
                    manufacturer=default_manufacturer,
                    posted = posted,
                    site=default_site,
                    valute=default_valute,
                    description=base_data.get("description", ""),
                    type=3 if len(group) > 1 else 1,
                    quantity=1000,
                    typeofchoice=1,
                    image=main_image,
                )

                if product is None:
                    total_errors += 1
                    continue

                if existed:
                    total_updated += 1
                else:
                    total_created += 1

                # Обновляем категории
                if "category" in base_data and pd.notna(base_data["category"]):
                    categories = get_or_create_categories_from_path(
                        base_data["category"], default_site
                    )
                    product.category.set(categories)

                # Обновляем атрибуты размеров
                all_sizes = set()
                for row in group:
                    sizes_str = row.get("sizes", "")
                    if sizes_str and isinstance(sizes_str, str):
                        sizes = [
                            s.strip() for s in sizes_str.replace(";", ",").split(",") if s.strip()
                        ]
                        all_sizes.update(sizes)

                # Очищаем старые атрибуты и добавляем новые
                product.atribute.clear()
                for size_val in all_sizes:
                    attr = find_size_attributes_for_value(size_val, numeric_attrs, letter_attrs)
                    if attr:
                        product.atribute.add(attr)

                product.save()

                # Обновляем галерею
                update_product_gallery(product, image_urls)

                # Обрабатываем цены и вариации
                if len(group) == 1:
                    # Простой продукт
                    price_value = parse_price(base_data.get("Цена: Цена продажи", 0))

                    # Обновляем или создаем цену
                    price_obj = ProductsPrice.objects.filter(product=product).first()
                    if price_obj:
                        price_obj.price = price_value
                        price_obj.save()
                    else:
                        price_obj = ProductsPrice.objects.create(
                            product=product,
                            price=price_value,
                        )

                    product.price_item = price_obj
                    product.price = price_value
                    product.save()

                    print(f"💰 Обновлена цена: {product.name} - {price_value}")

                else:
                    # Вариативный продукт
                    print(f"🔧 Обрабатываем вариации для: {product.name}")

                    for variation in group:
                        price_value = parse_price(variation.get("Цена: Цена продажи", 0))
                        update_or_create_variation(
                            product, variation, price_value,
                            numeric_attrs, letter_attrs, default_site
                        )

            except Exception as e:
                print(f"❌ Ошибка при обработке группы {key}: {e}")
                total_errors += 1
                continue

        print(f"\n📊 Итоги импорта:")
        print(f"✅ Создано новых продуктов: {total_created}")
        print(f"🔄 Обновлено существующих продуктов: {total_updated}")
        print(f"❌ Ошибок: {total_errors}")
        print(f"📦 Всего обработано: {total_created + total_updated}")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
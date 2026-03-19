import os
import sys
import csv
import django
import requests
import re
from io import BytesIO
from decimal import Decimal, InvalidOperation
from django.utils.text import slugify
from decimal import ROUND_HALF_UP

# Инициализация Django
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_project.settings")
django.setup()

from shop.models import Products, Categories, Manufacturers, Valute
from django.contrib.sites.models import Site


def clean_price(price_str):
    """
    Очищаем и конвертируем цену в Decimal с 2 знаками после запятой.
    Возвращает Decimal или None, если не удалось.
    """
    if not price_str:
        return None

    cleaned = re.sub(r"[^\d.,]", "", price_str)
    cleaned = cleaned.replace(",", ".")

    try:
        dec = Decimal(cleaned).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return dec
    except InvalidOperation:
        print(f"⚠️ Некорректная цена '{price_str}', пропускаем товар.")
        return None


def get_or_create_category_by_name(name, parent=None, site=None):
    """
    Ищет категорию строго по name. Если не находит — создаёт новую.
    Устанавливает publishet=True и добавляет site (если указан).
    """
    name = name.strip()
    cat = Categories.objects.filter(name=name).first()
    found = 1 if cat else 0
    print(f"Категория '{name}': найдено = {found}")

    if cat:
        return cat
    else:
        cat = Categories.objects.create(
            name=name, slug=slugify(name), parent=parent, publishet=True
        )
        if site:
            cat.site.add(site)
        print(f"Создана новая категория '{name}' (id={cat.id})")
        return cat


def get_or_create_category_with_parent(cat_str):
    """
    Обрабатывает строку с категориями и создаёт их только при необходимости.
    Устанавливает publishet=True и site=3 для новых.
    Возвращает список категорий.
    """
    categories = []
    site = Site.objects.filter(id=3).first()

    if not site:
        print("❗ Не найден сайт с ID=3")
        return []

    parts = [p.strip() for p in cat_str.split(",") if p.strip()]

    for part in parts:
        if ">" in part:
            parent_name, child_name = [x.strip() for x in part.split(">", 1)]

            parent_cat = get_or_create_category_by_name(parent_name, site=site)
            child_cat = get_or_create_category_by_name(
                child_name, parent=parent_cat, site=site
            )

            categories.extend([parent_cat, child_cat])
        else:
            cat = get_or_create_category_by_name(part, site=site)
            categories.append(cat)

    return list(set(categories))


def download_image(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            filename = url.split("/")[-1]
            return filename, BytesIO(response.content)
    except Exception as e:
        print(f"Ошибка загрузки изображения {url}: {e}")
    return None, None


def import_products_from_csv(csv_path):
    manufacturer = Manufacturers.objects.first()
    valute = Valute.objects.first()
    site = Site.objects.filter(id=3).first()

    if not all([manufacturer, valute, site]):
        print("❗ Проверьте наличие Manufacturer, Valute и Site с ID=3")
        return

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            name = row.get("title", "").strip()
            fragment = row.get("description", "").strip()
            category_str = row.get("category", "").strip()
            image_url = row.get("image", "").strip()
            price_str = row.get("price", "").strip()

            if not name:
                print("⚠️ Пропущена строка без названия")
                continue

            price = clean_price(price_str)
            if price is None:
                print(
                    f"⚠️ Пропускаем товар '{name}' из-за некорректной цены '{price_str}'"
                )
                continue

            slug = slugify(name)

            categories = get_or_create_category_with_parent(category_str)

            product = Products(
                name=name,
                fragment=fragment,
                quantity=1000,
                type=1,
                typeofchoice=1,
                manufacturers=manufacturer,
                valute=valute,
                slug=slug,
                price=price,
            )

            if image_url:
                filename, image_data = download_image(image_url)
                if filename and image_data:
                    product.image.save(filename, image_data, save=False)

            try:
                product.save()
            except Exception as e:
                print(f"❗ Ошибка при сохранении продукта '{name}': {e}")
                continue

            product.category.add(*categories)
            product.site.add(site)

            print(f"✅ Создан продукт: {name} — {price}₸")


if __name__ == "__main__":
    csv_file = "wc-product.csv"  # путь к CSV
    import_products_from_csv(csv_file)

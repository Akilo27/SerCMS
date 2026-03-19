import os
import sys
import re
import django
import xml.etree.ElementTree as ET
from uuid import uuid4
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.utils.text import slugify
import requests

# --- Django setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_project.settings")
django.setup()

from django.contrib.sites.models import Site
from shop.models import Products, Categories, Valute, Atribute, Variable


RESERVED_FIELDS = {
    "Общая площадь",
    "Материал",
    "Число этажей",
    "Мансарда",
    "Цоколь",
    "Наружные стены",
    "Фундамент",
    "Перекрытия",
    "Тип кровли",
    "Покрытие кровли",
    "Наружная отделка",
}


def looks_numeric(value: str) -> bool:
    """Грубая эвристика: значение похоже на числовое (число с опц. ед. измерения)."""
    if not value:
        return False
    v = value.strip()
    v = v.replace(",", ".")
    return re.match(r"^\s*-?\d+(\.\d+)?(\s|$)", v) is not None


def import_products_from_xml(xml_file_path: str):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    site = Site.objects.first()
    valute_rub = Valute.objects.first()

    # Категория проектов
    category, _ = Categories.objects.get_or_create(
        name="Проекты",
        defaults={"slug": "proekty"},
    )

    for good in root.findall("good"):
        image_url = good.find("image").text if good.find("image") is not None else None

        # Собираем поля good -> {name: text}
        fields_data = {f.get("name"): (f.text or "").strip() for f in good.findall("field")}

        # --- Продукт ---
        article_raw = (fields_data.get("Артикул") or "").strip()
        if article_raw:
            product, _ = Products.objects.update_or_create(
                article=article_raw,
                defaults={
                    "name": fields_data.get("Название", ""),
                    "description": (fields_data.get("Планы помещений", "") or ""),
                    "fragment": (fields_data.get("Фасады", "") or ""),
                    "price": float((fields_data.get("Цена") or "0").replace(",", ".") or 0),
                    "valute": valute_rub,
                    "quantity": 0,
                    "type": 1,
                    "typeofchoice": 1,
                    "position": 0,
                    "review_rating": 0,
                    "review_count": 0,
                    "review_all_sum": 0,
                    "price_old": 0,
                    "price_seller": float((fields_data.get("Цена") or "0").replace(",", ".") or 0),
                    "costprice": float((fields_data.get("Цена") or "0").replace(",", ".") or 0) * 0.7,
                    "manufacturer_identifier": 0,
                    "generic_atribute": False,
                    "stocks": False,
                    "order": True,
                    "review": True,
                    "reklama": True,
                    "faqs": True,
                    "comment": True,
                    "weight": 0,
                    "width": 0,
                    "height": 0,
                    "length": 0,
                },
            )
        else:
            gen_article = f"AUTO-{uuid4().hex[:8]}"
            product, _ = Products.objects.update_or_create(
                article=gen_article,
                defaults={
                    "name": fields_data.get("Название", ""),
                    "description": (fields_data.get("Планы помещений", "") or ""),
                    "fragment": (fields_data.get("Фасады", "") or ""),
                    "price": float((fields_data.get("Цена") or "0").replace(",", ".") or 0),
                    "valute": valute_rub,
                    "quantity": 1 if fields_data.get("Наличие") == "Да" else 0,
                    "type": 1,
                    "typeofchoice": 1,
                    "position": 0,
                    "review_rating": 0,
                    "review_count": 0,
                    "review_all_sum": 0,
                    "price_old": 0,
                    "price_seller": float((fields_data.get("Цена") or "0").replace(",", ".") or 0),
                    "costprice": float((fields_data.get("Цена") or "0").replace(",", ".") or 0) * 0.7,
                    "manufacturer_identifier": 0,
                    "generic_atribute": False,
                    "stocks": False,
                    "order": False,
                    "review": True,
                    "reklama": True,
                    "faqs": True,
                    "comment": True,
                    "weight": 0,
                    "width": 0,
                    "height": 0,
                    "length": 0,
                },
            )

        # Картинка
        if image_url:
            try:
                resp = requests.get(image_url, timeout=15)
                if resp.status_code == 200:
                    img_temp = NamedTemporaryFile(delete=True)
                    img_temp.write(resp.content)
                    img_temp.flush()
                    product.image.save(f"{product.article or uuid4().hex[:8]}.jpg", File(img_temp), save=False)
            except Exception as e:
                print(f"Ошибка загрузки изображения для {product.article}: {e}")

        product.save()
        product.category.add(category)
        if site:
            product.site.add(site)

        # --- Атрибуты только из RESERVED_FIELDS ---
        for field_name, field_value in fields_data.items():
            if field_name not in RESERVED_FIELDS or not field_value:
                continue

            var_defaults = {
                "slug": slugify(field_name)[:500] or slugify(f"{field_name}-{uuid4().hex[:6]}"),
                "type": 3 if looks_numeric(field_value) else 2,
                "variabletype": 1,
                "price": 0,
            }
            variable, _ = Variable.objects.get_or_create(name=field_name, defaults=var_defaults)
            if site:
                variable.site.add(site)

            attr, _ = Atribute.objects.get_or_create(
                variable=variable,
                name=field_value,
                defaults={"content": field_value},
            )
            product.atribute.add(attr)

        print(f"Импортирован продукт: {product.name} (Артикул: {product.article})")


if __name__ == "__main__":
    import_products_from_xml("plans.ru.xml")

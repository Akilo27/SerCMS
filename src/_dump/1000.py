import os
import django
import sys
import uuid
import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from urllib.parse import urlparse
from django.core.files.base import ContentFile

# Django settings
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_project.settings")
django.setup()

from shop.models import Products, Categories, Site, Manufacturers

# Читаем HTML-файл
base_dir = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(base_dir, "catalog.html")

with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

site_obj = Site.objects.get(id=3)

# Перебираем все элементы: категория или карточка товара
elements = soup.select(
    "div.tss-2t67l8-title-productGroupNameWrapper, div.tss-s50zji-productRowCardWrapper"
)

current_category = None

for el in elements:
    if "tss-2t67l8-title-productGroupNameWrapper" in el.get("class", []):
        # Найдена новая категория
        category_name = el.text.strip()
        current_category, _ = Categories.objects.get_or_create(name=category_name)
        current_category.publishet = True  # Устанавливаем опубликованной
        current_category.site.set([site_obj])
        current_category.save()
        print(f"\n[+] Обработка категории: {category_name}")

    elif "tss-s50zji-productRowCardWrapper" in el.get("class", []) and current_category:
        try:
            # Название товара
            name_tag = el.select_one(".tss-1k46j4r-nameWrapper")
            if not name_tag:
                continue
            name = name_tag.text.strip()

            # Цена
            price_tag = el.select_one(".tss-13bqvd4-price")
            if not price_tag:
                continue
            price_str = (
                price_tag.text.replace("\xa0", "").replace(" ", "").replace(",", ".")
            )
            price = Decimal(price_str)

            # Картинка
            image_tag = el.select_one("img[data-testid='-productRowCard-image']")
            image_url = image_tag["src"] if image_tag else ""
            image_content = None
            image_filename = None

            if image_url:
                response = requests.get(image_url)
                if response.status_code == 200:
                    image_ext = os.path.splitext(urlparse(image_url).path)[1] or ".jpg"
                    image_filename = f"{uuid.uuid4()}{image_ext}"
                    image_content = ContentFile(response.content, name=image_filename)

            # Артикул
            article_tag = el.select_one("div.tss-pymsqe-articleAndCode p")
            article = article_tag.text.strip() if article_tag else "Без артикула"

            # Количество (пока фиксировано)
            quantity = "1000"

            # Описание
            description = f"Артикул: {article}\nКоличество: {quantity}"

            # Создание продукта
            product = Products.objects.create(
                id=uuid.uuid4(),
                name=name,
                price=price,
                description=description,
                type=1,
                typeofchoice=1,
                manufacturers=Manufacturers.objects.first(),
                manufacturer_identifier=0,
            )

            if image_content:
                product.image.save(image_filename, image_content, save=False)

            product.save()
            product.category.add(current_category)
            product.site.set([site_obj])

            print(f"[✔] Добавлен продукт: {name}")

        except Exception as e:
            print(f"[!] Ошибка при добавлении товара: {e}")

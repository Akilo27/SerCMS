import os
import django
import sys
from bs4 import BeautifulSoup

# Django settings
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_project.settings")
django.setup()

from shop.models import Products, Categories, Site

# Читаем HTML-файл
base_dir = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(base_dir, "catalog.html")

with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

site_obj = Site.objects.get(id=1)

# Перебираем все элементы: категория или карточка товара
elements = soup.select(
    "div.tss-2t67l8-title-productGroupNameWrapper, div.tss-s50zji-productRowCardWrapper"
)

current_categories = []

for el in elements:
    if "tss-2t67l8-title-productGroupNameWrapper" in el.get("class", []):
        # Найдена категория — пробуем найти все подходящие
        category_name = el.text.strip()
        matched_categories = Categories.objects.filter(name=category_name)

        if matched_categories.exists():
            current_categories = list(matched_categories)
            print(
                f"\n[−] Найдено категорий с именем '{category_name}': {len(current_categories)}"
            )
        else:
            current_categories = []
            print(f"[!] Категория не найдена: {category_name}")

    elif (
        "tss-s50zji-productRowCardWrapper" in el.get("class", []) and current_categories
    ):
        try:
            # Название товара
            name_tag = el.select_one(".tss-1k46j4r-nameWrapper")
            if not name_tag:
                continue
            name = name_tag.text.strip()

            found = False
            for cat in current_categories:
                product = Products.objects.filter(name=name, category=cat).first()
                if product:
                    product.delete()
                    print(f"[✘] Удалён продукт: {name} (категория: {cat.name})")
                    found = True
                    break

            if not found:
                print(f"[!] Продукт не найден: {name}")

        except Exception as e:
            print(f"[!] Ошибка при удалении товара: {e}")

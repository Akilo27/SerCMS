import os
import sys
import django
from bs4 import BeautifulSoup
from django.utils.text import slugify
import uuid

# --- Django setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_project.settings")
django.setup()

from django.contrib.auth import get_user_model
from webmain.models import Price, PriceInfo  # Убедитесь, что путь к моделям правильный
from django.contrib.sites.models import Site

User = get_user_model()

# --- Настройки ---
html_file_path = "price.html"  # путь к вашему HTML-файлу
current_user = User.objects.first()
default_site = Site.objects.filter(id=1).first()

if not default_site:
    print("❌ Сайт с ID=1 не найден.")
    sys.exit(1)

# --- Парсим HTML-файл ---
with open(html_file_path, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

rows = soup.find_all("tr")
current_price = None

# --- Обрабатываем строки таблицы ---
for row in rows:
    cols = row.find_all("td")

    # Если строка — это заголовок раздела (одна ячейка и <strong>)
    if len(cols) == 1 and cols[0].find("strong"):
        section_name = cols[0].get_text(strip=True)
        slug = slugify(section_name)

        # Создаем новый Price для раздела
        current_price = Price.objects.create(
            author=current_user,
            name=section_name,
            slug=f"{slug}-{uuid.uuid4().hex[:6]}",  # уникализируем slug
            publishet=True,
        )
        current_price.site.add(default_site)
        current_price.save()
        print(f"\n🔷 Создан раздел: {section_name}")

    # Если строка — это услуга
    elif len(cols) >= 4 and current_price:
        name = cols[1].get_text(strip=True)
        meaning = cols[2].get_text(strip=True)
        amount = cols[3].get_text(strip=True)

        if name and amount:
            PriceInfo.objects.create(
                price=current_price,
                name=name,
                description=f"{name} ({meaning})" if meaning else name,
                amount=amount,
                meaning=meaning or "-",
            )
            print(f"   ✅ Услуга: {name} — {amount} ({meaning})")

print("\n🎉 Импорт завершён.")

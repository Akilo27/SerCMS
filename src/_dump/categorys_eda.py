import os
import sys
import django

# Устанавливаем путь к корню проекта
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "_project.settings"
)  # Замените на ваш settings-модуль

# Инициализация Django
django.setup()

from shop.models import Categories
from django.utils.text import slugify
from django.contrib.sites.models import Site

# Получаем нужные сайты по id
site_ids = [1]
sites = Site.objects.filter(id__in=site_ids)

# Структура категорий
category_tree = {
    "Пицца": [
        "Классическая пицца",
        "Пицца с морепродуктами",
        "Пицца с мясом",
        "Пицца с курицей",
        "Пицца вегетарианская",
        "Пицца с сыром",
        "Мини-пиццы",
    ],
    "Роллы/Суши": [
        "Классические роллы",
        "Запечённые роллы",
        "Темпура роллы",
        "Суши с рыбой",
        "Суши с морепродуктами",
        "Сеты",
        "Гунканы",
    ],
    "Бургеры": [
        "Классические бургеры",
        "Чизбургеры",
        "Бургеры с курицей",
        "Бургеры с рыбой",
        "Вегетарианские бургеры",
        "Мини-бургеры",
        "Авторские бургеры",
    ],
    "Выпечка": [
        "Хлеб",
        "Багеты",
        "Булочки",
        "Пироги",
        "Пирожки",
        "Слойки",
        "Торты и пирожные",
    ],
    "Фастфут": [
        "Шаурма",
        "Хот-доги",
        "Картофель фри",
        "Наггетсы",
        "Крылышки",
        "Сэндвичи",
        "Комбо-наборы",
    ],
    "Напитки": [
        "Газированные напитки",
        "Соки и нектары",
        "Вода",
        "Энергетики",
        "Чай",
        "Кофе",
        "Молочные коктейли",
    ],
    "Десерты": [
        "Торты",
        "Пирожные",
        "Мороженое",
        "Маффины и капкейки",
        "Эклеры и профитроли",
        "Желе и муссы",
        "Фруктовые десерты",
    ],
}

# Создание всех категорий
for main_name, subcats in category_tree.items():
    main_category, created = Categories.objects.get_or_create(
        name=main_name,
        defaults={
            "slug": slugify(main_name),
            "publishet": True,
            "count_product": 0,
        },
    )
    main_category.site.set(sites)
    print(f"{'✅' if created else '⚠️'} Главная категория: {main_name}")

    for sub_name in subcats:
        subcategory, created = Categories.objects.get_or_create(
            name=sub_name,
            parent=main_category,
            defaults={
                "slug": slugify(sub_name),
                "publishet": True,
                "count_product": 0,
            },
        )
        subcategory.site.set(sites)
        print(f"{'✅' if created else '⚠️'} └── Подкатегория: {sub_name}")

import os
import sys
import django

# Инициализация Django
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_project.settings")
django.setup()

from shop.models import Categories, Products


def update_category_product_counts():
    # Получаем все категории
    all_categories = Categories.objects.all()

    updated_count = 0

    for category in all_categories:
        # Подсчёт продуктов, у которых указана эта категория
        product_count = Products.objects.filter(category=category).count()

        if category.count_product != product_count:
            category.count_product = product_count
            category.save(update_fields=["count_product"])
            updated_count += 1
            print(f"✅ Обновлено: {category.name} — {product_count} товаров")

    print(f"\n✅ Обновлено {updated_count} категорий из {all_categories.count()}")


if __name__ == "__main__":
    update_category_product_counts()

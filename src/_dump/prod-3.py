import os
import sys
import django

# Инициализация Django
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_project.settings")
django.setup()

from shop.models import Products
from django.contrib.sites.models import Site


def delete_products_by_site(site_id):
    site = Site.objects.filter(id=site_id).first()
    if not site:
        print(f"❌ Сайт с id={site_id} не найден.")
        return

    products = Products.objects.filter(site=site)
    count = products.count()
    products.delete()
    print(f"✅ Удалено {count} продуктов, связанных с сайтом id={site_id}")


if __name__ == "__main__":
    delete_products_by_site(3)

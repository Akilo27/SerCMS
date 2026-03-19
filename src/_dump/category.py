import os
import django
import sys

# Django settings
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_project.settings")
django.setup()

from shop.models import Categories

# Обновляем все категории
updated_count = Categories.objects.update(publishet=True)

print(f"[✔] Обновлено категорий: {updated_count}")

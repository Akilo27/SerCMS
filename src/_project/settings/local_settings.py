from .core_settings import BASE_DIR
from pathlib import Path
import os.path
from environs import Env

DEBUG = True

STATIC_ROOT = BASE_DIR / '_staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / '_static'
]

env = Env()
env.read_env()

CSRF_TRUSTED_ORIGINS = ['https://nutsultan.com',
                        'https://*']
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        # "ENGINE": "django.db.backends.postgresql",  # Драйвер PostgreSQL
        # "NAME": env.str("POSTGRES_DB", "trendsup"),  # Имя БД
        # "USER": env.str("POSTGRES_USER", "trendsup"),  # Пользователь
        # "PASSWORD": env.str("POSTGRES_PASSWORD", "u4aPLQP1%s4R"),  # Пароль
        # "HOST": env.str("DJANGO_POSTGRES_HOST", "ifhayfusiepkar.beget.app"),  # Хост
        # "PORT": env.int("DJANGO_POSTGRES_PORT", 5432),  # Порт
    },
    'development_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'development.sqlite3',
    },
}


MEDIA_ROOT = os.path.join(BASE_DIR, '_media')



SMTP_FILE_PATH = Path(MEDIA_ROOT) / 'smtp.py'

try:
    with open(SMTP_FILE_PATH, 'r') as smtp_file:
        exec(smtp_file.read())  # Выполнить содержимое файла
except FileNotFoundError:
    pass
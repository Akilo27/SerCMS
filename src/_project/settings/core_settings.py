import os.path
from pathlib import Path
from string import ascii_lowercase, ascii_uppercase, digits

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
from environs import Env
from celery.schedules import crontab

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-qhdsxpk_%a=)u)+1a33+afe((@-ey#9oxgf^2dl*di1lp)d0jf"


env = Env()
env.read_env()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
# Application definition

INSTALLED_APPS = [
    'daphne',
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "silk",
    # "silk",
    "rosetta",
    "ckeditor",
    'channels',
    "ckeditor_uploader",

    #'debug_toolbar',
    "nested_admin",
    "django_ace",
    # app (Приложения)
    "webmain.apps.WebmainConfig",
    "moderation.apps.ModerationConfig",
    "useraccount.apps.UseraccountConfig",
    "payment.apps.PaymentConfig",
    "delivery.apps.DeliveryConfig",
    "chat.apps.ChatConfig",
    "documentation.apps.DocumentationConfig",
    "hr.apps.HrConfig",
    "kpi.apps.KpiConfig",
    "development.apps.DevelopmentConfig",
    "shop.apps.ShopConfig",
    "crm.apps.CrmConfig",
    "integration_import.apps.IntegrationImportConfig",
    "loyalty.apps.LoyaltyConfig",
    'django.contrib.humanize',
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    'hr.middleware.CurrentUserMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    #'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "_project.middleware.JWTAuthFromCookieMiddleware",
    "_project.middleware_country.CountryBasedLanguageMiddleware",
    "shop.mixins.CartMiddleware",
    "moderation.tracking_middleware.PageViewTrackingMiddleware",
]

ADMIN_URL = "developer_management/"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]


# Настройки CORS (разрешить Flutter доступ к API)
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "content-type",
    "Authorization",
    "X-API-KEY",
]
CORS_ALLOW_ALL_ORIGINS = True

CSRF_COOKIE_NAME = "csrftoken"  # Название cookie для CSRF токена


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        # Или если используется JWT:
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',  # Это может быть причиной ошибки
    ],
}




SECRET_API_TOKEN = "my-secret-token"


# Настройки JWT (по умолчанию)
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=11),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])


SITE_ID = 1

ROOT_URLCONF = "_project.urls"

X_FRAME_OPTIONS = "ALLOWALL"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "_templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "_project.wsgi.application"
ASGI_APPLICATION = '_project.asgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases


INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/


TIME_ZONE = "Europe/Moscow"

USE_I18N = True
USE_L10N = True

USE_TZ = True

AUTH_USER_MODEL = "useraccount.Profile"


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/


STATIC_URL = "/_static/"
STATICFILES_DIRS = ("_static",)
# STATIC_ROOT = os.path.join(BASE_DIR, '_static')

MEDIA_URL = "/_media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "_media")

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/
LOCALE_PATHS = [
    os.path.join(BASE_DIR, "locale"),
]
LANGUAGE_CODE = "ru"


ROSETTA_SHOW_AT_ADMIN_PANEL = True
ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS = True
ROSETTA_REQUIRES_AUTH = True


# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "csv_upload.log",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["file"],
        "level": "DEBUG",
    },
}
CKEDITOR_UPLOAD_PATH = "uploads/"

CKEDITOR_CONFIGS = {
    "default": {
        "skin": "moono",
        # 'skin': 'office2013',
        "toolbar_Basic": [["Source", "-", "Bold", "Italic"]],
        "toolbar_YourCustomToolbarConfig": [
            {
                "name": "document",
                "items": [
                    "Source",
                    "-",
                    "Save",
                    "NewPage",
                    "Preview",
                    "Print",
                    "-",
                    "Templates",
                ],
            },
            {
                "name": "clipboard",
                "items": [
                    "Cut",
                    "Copy",
                    "Paste",
                    "PasteText",
                    "PasteFromWord",
                    "-",
                    "Undo",
                    "Redo",
                ],
            },
            {"name": "editing", "items": ["Find", "Replace", "-", "SelectAll"]},
            {
                "name": "forms",
                "items": [
                    "Form",
                    "Checkbox",
                    "Radio",
                    "TextField",
                    "Textarea",
                    "Select",
                    "Button",
                    "ImageButton",
                    "HiddenField",
                ],
            },
            "/",
            {
                "name": "basicstyles",
                "items": [
                    "Bold",
                    "Italic",
                    "Underline",
                    "Strike",
                    "Subscript",
                    "Superscript",
                    "-",
                    "RemoveFormat",
                ],
            },
            {
                "name": "paragraph",
                "items": [
                    "NumberedList",
                    "BulletedList",
                    "-",
                    "Outdent",
                    "Indent",
                    "-",
                    "Blockquote",
                    "CreateDiv",
                    "-",
                    "JustifyLeft",
                    "JustifyCenter",
                    "JustifyRight",
                    "JustifyBlock",
                    "-",
                    "BidiLtr",
                    "BidiRtl",
                    "Language",
                ],
            },
            {"name": "links", "items": ["Link", "Unlink", "Anchor"]},
            {
                "name": "insert",
                "items": [
                    "Image",
                    "Flash",
                    "Table",
                    "HorizontalRule",
                    "Smiley",
                    "SpecialChar",
                    "PageBreak",
                    "Iframe",
                ],
            },
            "/",
            {"name": "styles", "items": ["Styles", "Format", "Font", "FontSize"]},
            {"name": "colors", "items": ["TextColor", "BGColor"]},
            {"name": "tools", "items": ["Maximize", "ShowBlocks"]},
            {"name": "about", "items": ["About"]},
            "/",  # put this to force next toolbar on new line
            {
                "name": "yourcustomtools",
                "items": [
                    # put the name of your editor.ui.addButton here
                    "Preview",
                    "Maximize",
                ],
            },
        ],
        "toolbar": "YourCustomToolbarConfig",  # put selected toolbar config here
        # 'toolbarGroups': [{ 'name': 'document', 'groups': [ 'mode', 'document', 'doctools' ] }],
        # 'height': 291,
        # 'width': '100%',
        # 'filebrowserWindowHeight': 725,
        # 'filebrowserWindowWidth': 940,
        # 'toolbarCanCollapse': True,
        # 'mathJaxLib': '//cdn.mathjax.org/mathjax/2.2-latest/MathJax.js?config=TeX-AMS_HTML',
        "tabSpaces": 4,
        "extraPlugins": ",".join(
            [
                "uploadimage",  # the upload image feature
                # your extra plugins here
                "div",
                "autolink",
                "autoembed",
                "embedsemantic",
                "autogrow",
                # 'devtools',
                "widget",
                "lineutils",
                "clipboard",
                "dialog",
                "dialogui",
                "elementspath",
            ]
        ),
    }
}


RANDOM_URL_CHARSET = f"{ascii_lowercase}{ascii_uppercase}{digits}"
RANDOM_URL_LENGTH = 32
RANDOM_URL_MAX_TRIES = 42

# EMAIL_HOST = 'smtp.beget.com'
# EMAIL_PORT = '465'
# EMAIL_USE_TSL = False
# EMAIL_USE_SSL = True
# EMAIL_HOST_USER = 'info@xn--80akffodct3a4h5a.xn--p1ai'
# #EMAIL_HOST_USER = 'info@памятьземли.рф'
# EMAIL_HOST_PASSWORD = 'OE%&K8s0'
# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "sessionid"
SESSION_COOKIE_AGE = 1209600  # 2 недели
SESSION_SAVE_EVERY_REQUEST = False


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("booking-redis", 6379)],
        },
    },
}

FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 1024 * 100  # 30 гигабайт
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 1024 * 100  # 30 гигабайт

# =====================
# CELERY
# =====================
CELERY_BROKER_URL = f"redis://{env.str('DJANGO_REDIS_HOST', 'localhost')}:6379/0"
CELERY_RESULT_BACKEND = f"redis://{env.str('DJANGO_REDIS_HOST', 'localhost')}:6379/1"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Moscow"  # или твой часовой пояс

# =====================
# CELERY LOGGING (по желанию)
# =====================
CELERYD_LOG_LEVEL = "DEBUG"
CELERYD_LOG_FORMAT = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
CELERYD_LOG_FILE = "/var/www/shop/celery.log"  # только если логировать в файл

# =====================
# CELERY BEAT
# =====================
CELERY_BEAT_SCHEDULE = {
    'check-hls-every-minute': {
        'task': 'webmain.tasks.check_pending_hls_files',
        'schedule': crontab(),  # каждая минута
    }
}

CELERY_IMPORTS = (
    'webmain.tasks',
)

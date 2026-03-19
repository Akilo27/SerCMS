from django.utils.translation import gettext_lazy as _
LANGUAGES = [
    ('ru', _('Русский')),
    ('en', _('Английский')),
    ('tg', _('Таджикский')),
    ('tr', _('Турецкий')),
    ('kk', _('Казахский')),
    ('uz', _('Узбекский')),
]
from django.conf.locale import LANG_INFO
LANG_INFO.update({
    'ru': {
        'bidi': False,
        'code': 'ru',
        'name': 'Русский',
        'name_local': 'Русский',
    },
    'en': {
        'bidi': False,
        'code': 'en',
        'name': 'Английский',
        'name_local': 'Английский',
    },
    'tg': {
        'bidi': False,
        'code': 'tg',
        'name': 'Таджикский',
        'name_local': 'Таджикский',
    },
    'tr': {
        'bidi': False,
        'code': 'tr',
        'name': 'Турецкий',
        'name_local': 'Турецкий',
    },
    'kk': {
        'bidi': False,
        'code': 'kk',
        'name': 'Казахский',
        'name_local': 'Казахский',
    },
    'tg': {
        'bidi': False,
        'code': 'tg',
        'name': 'Таджикский',
        'name_local': 'Таджикский',
    },
    'uz': {
        'bidi': False,
        'code': 'uz',
        'name': 'Узбекский',
        'name_local': 'Узбекский',
    },
})

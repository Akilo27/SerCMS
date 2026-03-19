from django import template
from django.template.loader import render_to_string
from development.models import SettingsModeration

from hr.models import HRChangeLog

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key.get('code')) if isinstance(dictionary, dict) else None



# Кастомный фильтр для проверки, заканчивается ли строка на указанный суффикс
@register.filter
def endswith(value, arg):
    """Проверка, заканчивается ли строка на указанный суффикс."""
    if isinstance(value, str):
        return value.endswith(arg)
    return False

@register.filter
def dict_get(obj, key):
    if isinstance(obj, dict):
        return obj.get(key)
    return None

@register.simple_tag
def last_five_hr_changes(user):
    return HRChangeLog.objects.filter(user=user).order_by("-time_change")[:5]

@register.simple_tag
def get_settings():
    """Возвращает объект настроек сайта"""
    return SettingsModeration.objects.first()


@register.simple_tag
def show_logo(size='normal', white=False):
    """
    Отображает логотип по заданным параметрам
    Параметры:
    - size: normal, lg, sm
    - white: True/False для белой версии
    """
    settings = SettingsModeration.objects.first()
    if not settings:
        return ""

    if white:
        if size == 'lg':
            field = settings.logo_white_lg
        elif size == 'sm':
            field = settings.logo_white_sm
        else:
            field = settings.logo_white
    else:
        if size == 'lg':
            field = settings.logo_lg
        elif size == 'sm':
            field = settings.logo_sm
        else:
            field = settings.logo

    if field:
        return field.url
    return ""


@register.simple_tag
def show_favicon():
    """Отображает фавикон"""
    settings = SettingsModeration.objects.first()
    return settings.favicon.url if settings and settings.favicon else ""


@register.inclusion_tag('tags/settings_info.html')
def show_settings_info():
    """Отображает основную информацию о настройках"""
    settings = SettingsModeration.objects.first()
    return {'settings': settings}


@register.simple_tag
def get_setting(setting_name):
    """Возвращает конкретную настройку по имени"""
    settings = SettingsModeration.objects.first()
    if not settings:
        return None

    return getattr(settings, setting_name, None)
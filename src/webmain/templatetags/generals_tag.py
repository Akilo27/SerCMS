from django import template
from django.contrib.sites.models import Site
from django.middleware.csrf import get_token
from webmain.forms import SubscriptionForm
from webmain.models import (
    SettingsGlobale,
    ContactPage,
    Pages,
)
import json

from useraccount.models import Notification

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Достает значение из словаря по ключу"""
    return dictionary.get(key, [])

@register.filter
def get_item(d, key):
    try:
        return d[str(key)]
    except Exception:
        try:
            return d[key]
        except Exception:
            return ""

@register.filter
def range_filter(value):
    """Создает диапазон от 1 до value+1"""
    return range(1, value + 1)

@register.filter
def mul(value, arg):
    """Умножает value на arg"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_settings(request):
    current_domain = request.get_host()
    try:
        current_site = Site.objects.get(domain=current_domain)
        settings = SettingsGlobale.objects.get(site=current_site)
        contact_phone_default = settings.contactpageinformation_set.filter(
            page_type="phone_default"
        ).first()
        contact_email_default = settings.contactpageinformation_set.filter(
            page_type="email_default"
        ).first()
        contact_address_default = settings.contactpageinformation_set.filter(
            page_type="address_default"
        ).first()
        contact_social_default = settings.contactpageinformation_set.filter(
            page_type="social_default"
        ).all()
        contact_works = settings.contactpageinformation_set.filter(
            page_type="works"
        ).all()
        contact_weekend = settings.contactpageinformation_set.filter(
            page_type="weekend"
        ).all()
        return {
            "setting": settings,
            "phone_default": contact_phone_default,
            "address_default": contact_address_default,
            "email_default": contact_email_default,
            "social_default": contact_social_default,
            "works": contact_works,
            "weekend": contact_weekend,
        }
    except SettingsGlobale.DoesNotExist:
        return None


@register.simple_tag
def get_json_template():
    """Парсит jsontemplate и возвращает список данных."""
    settings = SettingsGlobale.objects.first()
    if settings and settings.jsontemplate:
        try:
            return json.loads(settings.jsontemplate)
        except json.JSONDecodeError:
            return []
    return []


@register.simple_tag
def get_notifications_count(user):
    if user.is_authenticated:
        notification = Notification.objects.filter(user=user, status=1).first()
        if notification:
            return Notification.objects.filter(user=user, status=1).count()
    return 0


@register.simple_tag
def get_unread_notifications(user):
    if user.is_authenticated:
        return Notification.objects.filter(user=user, status=1).order_by("-created_at")[
            :4
        ]
    return []


@register.simple_tag
def get_likes_count(user):
    if user.is_authenticated:
        return user.bookmark.count()
    return 0


@register.filter
def get_contact(request):
    current_domain = request.get_host()
    try:
        current_site = Site.objects.get(domain=current_domain)
        settings = ContactPage.objects.filter(site=current_site).first()
        return settings
    except ContactPage.DoesNotExist:
        return None


# @register.simple_tag
# def get_address_default():
#     """Возвращает элементы с page_type='address_default'."""
#     addresses = ContactPageInformation.objects.filter(page_type="address_default")
#     return addresses

# @register.simple_tag
# def get_phone_default():
#     """Возвращает элементы с page_type='address_default'."""
#     phones = ContactPageInformation.objects.filter(page_type="phone_default")
#     return phones

# @register.simple_tag
# def get_email_default():
#     """Возвращает элементы с page_type='address_default'."""
#     emails = ContactPageInformation.objects.filter(page_type="email_default")
#     return emails

# @register.simple_tag
# def get_social_default():
#     """Возвращает элементы с page_type='address_default'."""
#     social = ContactPageInformation.objects.filter(page_type="social_default")
#     return social


@register.simple_tag
def get_field_info(page, field_name):
    """
    Получает информацию о конкретном поле по имени.
    :param page: Название страницы (например, 'home').
    :param field_name: Имя поля, которое ищем.
    :return: Значение `info` или None.
    """
    settings = SettingsGlobale.objects.first()
    if settings and settings.jsontemplate:
        try:
            data = json.loads(settings.jsontemplate)
            for item in data:
                if item.get("page") == page:
                    return item.get("fields", {}).get(field_name, {}).get("info")
        except json.JSONDecodeError:
            return None
    return None


@register.simple_tag
def get_contacts_first():
    return ContactPage.objects.first()


@register.simple_tag(takes_context=True)
def get_pages(context):
    request = context["request"]
    current_host = request.get_host()

    print(f"Текущий хост: {current_host}")  # Логируем в консоль

    try:
        current_site = Site.objects.get(domain__icontains=current_host.split(":")[0])
        print(f"Найден сайт: {current_site.domain}")  # Логируем найденный сайт

        pages = Pages.objects.filter(publishet=True, site__id=current_site.id)
        print(
            f"Найдено страниц: {pages.count()}"
        )  # Логируем количество найденных страниц

        for page in pages:
            print(
                f"Страница: {page.name}, Сайты: {[s.domain for s in page.site.all()]}"
            )

        return pages
    except Site.DoesNotExist:
        print("Сайт не найден!")
        return Pages.objects.none()


@register.simple_tag(takes_context=True)
def render_subscription_form(context):
    request = context["request"]
    form = SubscriptionForm()
    csrf_token = get_token(request)

    return {"form": form, "csrf_token": csrf_token}


#
# @register.simple_tag
# def get_address_default():
#     """Возвращает элементы с page_type='address_default'."""
#     addresses = ContactPageInformation.objects.filter(page_type="address_default")
#     return addresses
#
# @register.simple_tag
# def get_phone_default():
#     """Возвращает элементы с page_type='address_default'."""
#     phones = ContactPageInformation.objects.filter(page_type="phone_default")
#     return phones

# @register.simple_tag
# def get_email_default():
#     """Возвращает элементы с page_type='address_default'."""
#     emails = ContactPageInformation.objects.filter(page_type="email_default")
#     return emails

# @register.simple_tag
# def get_social_default():
#     """Возвращает элементы с page_type='address_default'."""
#     social = ContactPageInformation.objects.filter(page_type="social_default")
#     return social


@register.filter
def range_list(value):
    """
    Возвращает диапазон чисел от 1 до value включительно.
    """
    try:
        return range(1, int(value) + 1)
    except (ValueError, TypeError):
        return []

from django import template

from chat.models import ChatMessage
from useraccount.models import Notification


register = template.Library()


@register.simple_tag
def get_notifications_count(user):
    if user.is_authenticated:
        notification = Notification.objects.filter(user=user, status=1).first()
        if notification:
            return Notification.objects.filter(user=user, status=1).count()
    return 0

@register.simple_tag(takes_context=True)
def user_has_manufacturer(context):
    user = context["request"].user
    return user.is_authenticated and getattr(user, "manufacturers", None) is not None


@register.simple_tag
def count_unread_chats(user):
    """
    Возвращает количество чатов, где есть сообщения с статусом "Отправлено" (status=0),
    и текущий пользователь является участником чата.
    """
    if not user.is_authenticated:
        return 0  # Возвращаем 0 для неавторизованных пользователей

    # Ищем чаты, где есть сообщения со статусом 0 (непрочитанные) для данного пользователя
    unread_chats = (
        ChatMessage.objects.filter(
            status=0,  # Сообщения со статусом "Отправлено"
            chat__users=user,  # Пользователь должен быть участником чата
        )
        .values("chat")
        .distinct()
    )

    return unread_chats.count()


@register.simple_tag
def get_unread_notifications(user):
    if user.is_authenticated:
        return Notification.objects.filter(user=user, status=1).order_by("-created_at")[
            :4
        ]
    return []

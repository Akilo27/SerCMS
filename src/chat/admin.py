from django.contrib import admin
from .models import *

# Register your models here.


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = [
        "get_type_display",
        "owner",
        "display_administrators",
        "display_users",
        "created_at",
        "updated_at",
        "display_last_message",
    ]

    def display_administrators(self, obj):
        # Отображает администраторов через запятую
        return ", ".join([admin.username for admin in obj.administrators.all()])

    display_administrators.short_description = "Администраторы"

    def display_users(self, obj):
        # Отображает пользователей через запятую
        return ", ".join([user.username for user in obj.users.all()])

    display_users.short_description = "Пользователи"

    def display_last_message(self, obj):
        # Отображает содержимое последнего сообщения
        return obj.last_message.content if obj.last_message else "Нет сообщений"

    display_last_message.short_description = "Последнее сообщение"


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["chat", "content", "author", "display_views"]

    def display_views(self, obj):
        # Отображает пользователей через запятую
        return ", ".join([user.username for user in obj.views.all()])

    display_views.short_description = "Просмотреть"


@admin.register(ChatMessageMedia)
class ChatMessageMediaAdmin(admin.ModelAdmin):
    model = ChatMessageMedia

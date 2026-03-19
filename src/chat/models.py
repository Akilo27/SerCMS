from django.db import models
import uuid
import os
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.sites.models import Site


# Create your models here.


def chat_message_media_upload_to(instance, filename):
    # Получаем ID чата из связанного объекта ChatMessage
    chat_id = instance.comment.chat.id
    # Создаем уникальное имя файла, чтобы избежать конфликтов
    unique_filename = f"{uuid.uuid4()}_{filename}"
    # Возвращаем кастомный путь
    return os.path.join("chat", str(chat_id), unique_filename)


class Chat(models.Model):
    TYPE = [
        (1, "Групповой"),
        (2, "Личные"),
    ]

    type = models.PositiveSmallIntegerField("Тип", choices=TYPE, blank=False, default=1)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Владелец",
        on_delete=models.CASCADE,
        related_name="chatowner",
    )
    administrators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="Администраторы",
        related_name="chatadministrators",
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name="Пользователи", related_name="chatusers"
    )
    name = models.CharField(
        max_length=150, verbose_name="Название", blank=True, null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания", null=True, blank=True
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Дата последнего обновления", null=True, blank=True
    )

    # GenericForeignKey для связывания с любым объектом
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.TextField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    site = models.ManyToManyField(Site, verbose_name="Сайты", blank=True, default="1")

    # Связь с последним сообщением
    last_message = models.ForeignKey(
        "ChatMessage",
        verbose_name="Последнее сообщение",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="last_message_chat",  # Уникальное имя для обратной связи
    )

    def __str__(self):
        return self.name if self.name else f"Чат {self.id}"

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"


class ChatMessage(models.Model):
    STATUS_CHOICES = [
        (0, "Отправлено"),
        (1, "Прочитано"),
    ]
    status = models.SmallIntegerField(
        verbose_name="Статус", choices=STATUS_CHOICES, default=1
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        verbose_name="Чат",
        related_name="chatmessage",  # Убедитесь, что имя обратной связи уникально
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    content = models.TextField(verbose_name="Сообщение")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        blank=True,
        null=True,
    )
    views = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователи которые прочитали",
        related_name="viewsmessage",
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"

    def save(self, *args, **kwargs):
        # Сохраняем сообщение
        super().save(*args, **kwargs)
        # Обновляем поле last_message у связанного чата на текущий объект сообщения
        self.chat.last_message = self
        self.chat.updated_at = self.date  # Обновляем дату обновления чата
        self.chat.save()


class ChatMessageMedia(models.Model):
    comment = models.ForeignKey(
        ChatMessage, on_delete=models.CASCADE, related_name="chatmessagemedia"
    )
    file = models.FileField(upload_to="chat_message_media_upload_to/%Y/%m/%d/")
    filename = models.CharField("Имя", max_length=250, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.filename:
            self.filename = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Файл сообщений чата"
        verbose_name_plural = "Файлы сообщений чата"

from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator

# Create your models here.


class Lead(models.Model):
    STATUS_CHOICES = [
        ("new", "Новый"),
        ("contacted", "Связались"),
        ("qualified", "Квалифицирован"),
        ("lost", "Потерян"),
        ("converted", "Конвертирован"),
        ("at_work", "В работе"),
        ("passed", "Сдан"),
    ]
    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="new", verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Пользователь",
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="users_lead",
        verbose_name="Сотрудники",
    )
    procent = models.PositiveIntegerField(
        default=0, blank=True, null=True, verbose_name="Процент"
    )
    image = models.FileField(
        "Изображение",
        upload_to="lead/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    amount = models.DecimalField("Стоимость", max_digits=10, decimal_places=2)
    profit = models.DecimalField("Прибыль", max_digits=10, decimal_places=2)
    expenditure = models.DecimalField("Расход", max_digits=10, decimal_places=2)
    paid_out = models.DecimalField("Выплачено", max_digits=10, decimal_places=2)
    swim_out = models.DecimalField("К выплате", max_digits=10, decimal_places=2)
    payment = models.ManyToManyField("StatusPayment", verbose_name="Платеж")

    def __str__(self):
        return self.name

    def at_work_tasks_count(self):
        return self.task_set.filter(type="at_work").count()

    def complite_tasks_count(self):
        return self.task_set.filter(type="complite").count()

    class Meta:
        verbose_name = "Лид"
        verbose_name_plural = "Лиды"


class Leaddocement(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Пользователь",
    )
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    created_at = models.DateTimeField(auto_now_add=True)
    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Лид"
    )
    file = models.FileField(
        "Документ", upload_to="lead/%Y/%m/%d/", blank=True, null=True
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"


class Task(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Низкий"),
        ("medium", "Средний"),
        ("high", "Высокий"),
    ]
    TASK_TYPE_CHOICES = [
        ("at_work", "В работе"),
        ("complite", "Завершен"),
        ("pending_review", "Ожидающий рассмотрения"),
    ]
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Пользователь",
    )
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    type = models.CharField(
        max_length=20, choices=TASK_TYPE_CHOICES, verbose_name="Тип"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="medium",
        verbose_name="Приоритет",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    due_date = models.DateTimeField(verbose_name="Срок исполнения")
    notes = models.TextField(blank=True, verbose_name="Комментарий")
    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Лид"
    )
    amount = models.DecimalField("Стоимость", max_digits=10, decimal_places=2)
    payment = models.ForeignKey(
        "StatusPayment",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Платеж",
    )
    position = models.PositiveIntegerField(default=0, verbose_name="Позиция")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ['position']  # Сортировка по позиции


class StatusPayment(models.Model):
    STATUS_CHOICES = [
        ("payout", "Выплата"),
        ("replenishment", "Пополнение"),
    ]
    amount = models.DecimalField("Стоимость", max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, verbose_name="Описание")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="new", verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"


class Deal(models.Model):
    STAGE_CHOICES = [
        ("prospecting", "В процесе"),
        ("proposal", "Отправленное предложение"),
        ("negotiation", "Переговоры"),
        ("won", "Сдан"),
        ("lost", "Не сдан"),
    ]
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    stage = models.CharField(
        max_length=20, choices=STAGE_CHOICES, default="prospecting", verbose_name="Этап"
    )
    expected_close_date = models.DateTimeField(
        null=True, blank=True, verbose_name="Ожидаемая дата закрытия"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Задача"
    )
    position = models.PositiveIntegerField(default=0, verbose_name="Позиция")
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='children',
        verbose_name="Родительская сделка"
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Сделка"
        verbose_name_plural = "Сделки"
        ordering = ['position']  # Сортировка по позиции


class Note(models.Model):
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Лид"
    )

    def __str__(self):
        return self.content

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

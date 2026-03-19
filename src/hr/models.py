from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from ckeditor.fields import RichTextField
import uuid
import os

from shop.models import Manufacturers


# Create your models here.
class Schedule(models.Model):
    PAGETYPE = [
        (1, "Blue", "bg-primary"),
        (2, "Gray Dark", "bg-secondary"),
        (3, "Green", "bg-success"),
        (4, "Cyan", "bg-info"),
        (5, "Yellow", "bg-warning"),
        (6, "Red", "bg-danger"),
        (7, "Dark", "bg-dark"),
    ]
    pagetype = models.PositiveSmallIntegerField(
        "Тип",
        choices=[
            (item[0], item[1]) for item in PAGETYPE
        ],  # Используем только (id, name)
        blank=False,
        default=1,
    )
    created_at = models.DateTimeField("Дата создание", auto_now_add=True)
    data_start = models.DateField("Дата начало", blank=True, null=True )
    data_end = models.DateField("Дата конца", blank=True, null=True)
    time_start = models.TimeField("Время начало", blank=True, null=True)
    time_end = models.TimeField("Время конца", blank=True, null=True)
    name = models.CharField("Название", max_length=250)
    description = models.TextField("Описание", db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Пользователь", on_delete=models.CASCADE
    )

    @property
    def pagetype_class(self):
        return self.get_pagetype_class()

    @classmethod
    def get_pagetype_choices(cls):
        """Возвращает список категорий с их CSS-классами"""
        return [
            {"id": item[0], "name": item[1], "css_class": item[2]}
            for item in cls.PAGETYPE
        ]

    def get_pagetype_class(self):
        # Используем только id и css_class
        return dict((item[0], item[2]) for item in self.PAGETYPE).get(
            self.pagetype, "bg-primary"
        )

    class Meta:
        verbose_name = "График"
        verbose_name_plural = "Графики"

class WorkShift(models.Model):
    WORK_STATUS = [
        ("1", "Выход"),  # начало смены
        ("2", "Уход"),   # окончание смены
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="work_shifts",
        verbose_name="Пользователь"
    )

    # Время выхода на смену
    date_start = models.DateField("Дата выхода на смену", blank=True, null=True)
    time_start = models.TimeField("Время выхода на смену", blank=True, null=True)

    # Время ухода со смены
    date_end = models.DateField("Дата ухода со смены", blank=True, null=True)
    time_end = models.TimeField("Время ухода со смены", blank=True, null=True)

    # Фото и видео при выходе
    photo_accept_place = models.ImageField(
        "Фото принятия рабочего места", upload_to="work_shifts/accept/", blank=True, null=True
    )
    photo_entry_place = models.ImageField(
        "Фото выхода на рабочее место", upload_to="work_shifts/entry/", blank=True, null=True
    )
    selfie_entry = models.ImageField(
        "Собственное фото (приход)", upload_to="work_shifts/selfies/", blank=True, null=True
    )
    video_entry = models.FileField(
        "Видео фиксации прихода", upload_to="work_shifts/video_entry/", blank=True, null=True
    )

    # Фото и видео при уходе
    photo_handover_place = models.ImageField(
        "Фото сдачи рабочего места", upload_to="work_shifts/handover/", blank=True, null=True
    )
    photo_exit_place = models.ImageField(
        "Фото ухода с рабочего места", upload_to="work_shifts/exit/", blank=True, null=True
    )
    selfie_exit = models.ImageField(
        "Собственное фото (уход)", upload_to="work_shifts/selfies/", blank=True, null=True
    )
    video_exit = models.FileField(
        "Видео фиксации ухода", upload_to="work_shifts/video_exit/", blank=True, null=True
    )

    work_status = models.CharField(
        "Тип", max_length=20, choices=WORK_STATUS, default="1"
    )

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        verbose_name = "Выход/уход со смены"
        verbose_name_plural = "Выходы/уходы со смены"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_work_status_display()} — {self.user} ({self.date_start or self.date_end})"



class Vacancy(models.Model):
    WORK_SCHEDULE_CHOICES = [
        ("1", "Полный рабочий день"),
        ("2", "Неполный рабочий день"),
        ("3", "Удаленная работа"),
        ("4", "Сменный график"),
    ]

    work_schedule = models.CharField(
        "График работы", max_length=20, choices=WORK_SCHEDULE_CHOICES, default="1"
    )
    title = models.CharField("Название вакансии", max_length=255)
    description = models.TextField("Описание вакансии")
    requirements = models.TextField("Требования к кандидату")
    salary = models.DecimalField(
        "Заработная плата", max_digits=10, decimal_places=2, null=True, blank=True
    )
    location = models.CharField("Местоположение", max_length=255, null=True, blank=True)
    posted_at = models.DateTimeField("Дата размещения вакансии", auto_now_add=True)
    is_active = models.BooleanField("Активность вакансии", default=True)
    image = models.FileField(
        "Картинка",
        upload_to="vacancy/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    site = models.ManyToManyField(Site, verbose_name="Сайты", blank=True, default="1")
    slug = models.SlugField(max_length=140)
    create = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"


class VacancyResponse(models.Model):
    vacancy = models.ForeignKey(
        "Vacancy", on_delete=models.CASCADE, related_name="responses"
    )
    full_name = models.CharField("ФИО", max_length=255)
    email = models.EmailField("Email")
    phone = models.CharField("Телефон", max_length=20)
    message = models.TextField("Сообщение", blank=True, null=True)
    resume = models.FileField(
        "Резюме", upload_to="resumes/%Y/%m/%d/", null=True, blank=True
    )
    create = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} — {self.vacancy.title}"


class HRChangeLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType,
                                     on_delete=models.CASCADE)  # тип (модель), к которой относится запись лога
    field_name = models.CharField(max_length=100, verbose_name="Изменённое поле")
    old_value = models.TextField(verbose_name="Старое значения", blank=False)
    new_value = models.TextField(verbose_name="Новое значения", blank=False)
    time_change = models.DateTimeField(verbose_name="Время изменения", auto_now_add=True)
    object_id = models.CharField(max_length=100)
    content_object = GenericForeignKey('content_type', 'object_id')  # Ссылка на конткретный обьект

    def __str__(self):
        return f"{self.user} - {self.content_object}"

    class Meta:
        verbose_name = 'Изменение'
        verbose_name_plural = 'Изменении'

class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time = models.PositiveIntegerField(default=0, verbose_name="Длительность")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="lesson_owner",
        verbose_name="Владелец",
    )
    assistant = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="lesson_assistant",
        verbose_name="Пользователи",
    )
    price = models.DecimalField(
        default=0.00,
        max_digits=11,
        decimal_places=2,  # Было 0
        verbose_name="Цена",
    )
    quantity_files = models.PositiveIntegerField(default=0, verbose_name="Количество файлов")
    quantity_tests = models.PositiveIntegerField(default=0, verbose_name="Количество тестов")
    quantity_video = models.PositiveIntegerField(default=0, verbose_name="Количество видео")
    name = models.CharField("Название", max_length=250)
    manufacturers = models.ManyToManyField(
        to=Manufacturers,
        verbose_name="Производитель",
    )
    cover = models.FileField(
        "Обложка",
        upload_to="lesson/%Y/%m/%d/",
        blank=True,
        null=True,
        default="default/blogs/cover.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    image = models.FileField(
        "Изображение",
        upload_to="lesson/%Y/%m/%d/",
        blank=True,
        null=True,
        default="default/blogs/cover.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    description = RichTextField("Описание", db_index=True)
    slug = models.SlugField(max_length=140, unique=True)
    previev = models.FileField(
        upload_to="pages/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Превью",
        default="default/imagegallery/imagegellery_images.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    title = models.CharField(
        verbose_name="Мета-заголовок",
        max_length=150,
        blank=True,
        null=True,
    )
    metadescription = models.CharField(
        verbose_name="Мета-описание",
        max_length=255,
        blank=True,
        null=True,
    )
    propertytitle = models.CharField(
        verbose_name="Мета-заголовок ссылки",
        max_length=150,
        blank=True,
        null=True,
    )
    propertydescription = models.CharField(
        verbose_name="Мета-описание ссылки",
        max_length=255,
        blank=True,
        null=True,
    )
    public = models.BooleanField("Доступен всем", default=False)
    publishet = models.BooleanField("Опубликован", default=False)
    resources = models.TextField(verbose_name='Ресурсы', default='[]')

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"

    def __str__(self):
        return self.name


class TestResult(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="test_results", verbose_name="Урок")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Оценка")
    total_questions = models.PositiveIntegerField(default=0, verbose_name="Общее количество вопросов")
    correct_answers = models.PositiveIntegerField(default=0, verbose_name="Правильные ответы")
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата завершения")
    resources = models.TextField(verbose_name='Ресурсы', default='[]')

    def __str__(self):
        return f"Результат для {self.user} в уроке {self.lesson.name}"

    class Meta:
        verbose_name = "Результат тестирования"
        verbose_name_plural = "Результаты тестирования"


class LessonMaterial(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="materials",blank=True, null=True, verbose_name="Урок")
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='lesson/', blank=True)
    new_file = models.FileField(upload_to='', blank=True, null=True, editable=False)
    original_filename = models.CharField("Оригинальное имя файла", max_length=255, blank=True, null=True, editable=False)
    temp_file_id = models.CharField("ID временного файла", max_length=64, blank=True, null=True, editable=False)
    create = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    uploaded_size = models.PositiveIntegerField(default=0,blank=True, null=True, editable=False)
    size = models.PositiveIntegerField(null=True, blank=True, editable=False)
    active = models.BooleanField("Загружено", default=False)

    def __str__(self):
        return f"{self.original_filename or self.file.name} ({self.size} bytes)"

    def file_type(self):
        ext = os.path.splitext(self.file.name)[-1].lower()
        if ext in ['.mp4', '.webm', '.mov']:
            return 'video'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
            return 'image'
        elif ext == '.pdf':
            return 'pdf'
        return 'other'

    class Meta:
        verbose_name = "Материал урока"
        verbose_name_plural = "Материалы урока"


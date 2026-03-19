from django.db import models
from ckeditor.fields import RichTextField
from django.core.validators import FileExtensionValidator
import os
from django.core.exceptions import ValidationError
from multiselectfield import MultiSelectField


# Create your models here.
class ThemesCastegorys(models.Model):
    name = models.CharField("Название", max_length=250)
    description = RichTextField("Описание", db_index=True)
    slug = models.SlugField(max_length=140)
    cover = models.FileField(
        "Обложка",
        upload_to="themes/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    icon = models.FileField(
        "Иконка",
        upload_to="themes/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    image = models.FileField(
        "Картинка",
        upload_to="themes/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    publishet = models.BooleanField("Опубликован", default=False)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания", blank=True, null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Дата обновления", blank=True, null=True
    )

    class Meta:
        verbose_name = "Категория темы"
        verbose_name_plural = "Категории темы"


class Themes(models.Model):
    categorys = models.ForeignKey(
        ThemesCastegorys,
        verbose_name="Категория темы",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    name = models.CharField("Название", max_length=250)
    description = RichTextField("Описание", db_index=True)
    slug = models.SlugField(max_length=140, unique=True)
    cover = models.FileField(
        "Обложка",
        upload_to="blogs/%Y/%m/%d/",
        blank=True,
        null=True,
        default="default/blogs/cover.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    version = models.CharField(
        max_length=150, verbose_name="Версия", blank=True, null=True
    )
    publishet = models.BooleanField("Опубликован", default=False)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания", blank=True, null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Дата обновления", blank=True, null=True
    )

    class Meta:
        verbose_name = "Тема"
        verbose_name_plural = "Темы"


class ThemesMedia(models.Model):
    themes = models.ForeignKey("Themes", on_delete=models.CASCADE, verbose_name="Тема")
    file = models.FileField(upload_to="ticket/%Y/%m/%d/tiket_file/")

    def get_file_name(self):
        return os.path.basename(self.file.name)

    class Meta:
        verbose_name = "Файл темы"
        verbose_name_plural = "Файлы темы"


class SettingsModeration(models.Model):
    logo = models.FileField(
        "Логотип",
        upload_to="settings/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    logo_lg = models.FileField(
        "Дополнительный логотип полный",
        upload_to="settings/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    logo_sm = models.FileField(
        "Дополнительный логотип маленький",
        upload_to="settings/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    logo_white = models.FileField(
        "Логотип белый",
        upload_to="settings/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    logo_white_lg = models.FileField(
        "Дополнительный белый полный",
        upload_to="settings/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    logo_white_sm = models.FileField(
        "Дополнительный логотип белый маленький",
        upload_to="settings/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    favicon = models.FileField(
        "Фавикон", upload_to='settings/%Y/%m/%d/', blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['png', 'webp', 'jpeg', 'jpg', 'svg'])]
    )
    name = models.CharField("Название", max_length=500, blank=True, null=True, default='Название сайта')
    buttom = models.CharField("Кнопка", max_length=500, blank=True, null=True)
    siddebar = models.CharField("Сайдбар", max_length=500, blank=True, null=True)
    TYPE_OPTIONS = (
        ("statistic", "Статистика"),
        ("groups", "Группы"),
        ("employees", "Сотрудники"),
        ("clients", "Клиенты"),
        ("knowledge_base", "База знаний"),
        ("email", "Email"),
        ("telephony", "Телефония"),
        ("projects", "Проекты"),
        ("completed_works", "Проделанные работы"),
        ("schedule", "График"),
        ("task_manager", "Задачник"),
        ("accounting", "Бухгалтерия"),
        ("payments", "Платежи"),
        ("requests", "Запросы"),
        ("household", "Хоз. часть"),
        ("lesson", "Урок"),
        ("training", "Обучение"),
        ("vacancies", "Вакансии"),
        ("applications", "Заявки"),
        ("warehouses", "Склады (Магазины)"),
        ("companies", "Компании"),
        ("products", "Товары"),
        ("categories", "Категории"),
        ("purchases", "Покупки"),
        ("complaints", "Жалобы"),
        ("reviews", "Отзывы"),
        ("comments", "Комментарии"),
        ("questions", "Вопросы"),
        ("variations", "Вариации"),
        ("currency", "Валюта"),
        ("support", "Поддержка"),
        ("tickets", "Тикеты"),
        ("appeal", "Обращение"),
        ("domains", "Домены"),
        ("loyalty_program", "Программа лояльности"),
        ("notifications", "Уведомления"),
        ("languages", "Языки"),
        ("integrations", "Интеграции"),
        ("blog", "Блог (Новости)"),
        ("pages", "Страницы"),
        ("charity", "Благотворительность"),
        ("gallery", "Галерея"),
        ("services", "Услуги"),
        ("price", "Прайс"),
        ("faq", "ЧаВо"),
        ("documentation", "Документация"),
        ("personal", "Личные"),
    )

    types = MultiSelectField(
        choices=TYPE_OPTIONS,
        blank=True,
        verbose_name="Доступ",
        default=list,
        null=True,
        max_length=255,
    )
    def clean(self):
        if SettingsModeration.objects.exists() and not self.pk:
            raise ValidationError('Можно создать только один объект настроек сайта.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or "Настройки сайта"

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"


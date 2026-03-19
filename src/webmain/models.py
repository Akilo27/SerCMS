from django.db import models
from django.urls import reverse
from django.conf import settings
from django.core.validators import FileExtensionValidator
import os
from django.contrib.sites.models import Site
from django.utils.html import strip_tags
from moderation.models import Stopwords
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from ckeditor.fields import RichTextField

from shop.models import Manufacturers


class Seo(models.Model):
    """Персона"""

    PAGE_CHOICE = [
        (1, "Новости"),
        (2, "Поиск"),
        (3, "Контакты"),
        (4, "ЧаВО"),
        (5, "Авторизация"),
        (6, "Регистрация"),
        (7, "Сбросить пароль"),
        (8, "Профиль"),
        (9, "Сменить пароль"),
        (10, "Паспортные данные"),
        (11, "Уведомление"),
        (12, "Объявление"),
        (13, "Благотворительность"),
        (14, "Брони"),
        (14, "Чаты"),
        (15, "Галерея"),
        (16, "Услуги"),
        (17, "Прайс"),
        (18, "Магазин"),
        (19, "Вакансии"),
        (20, "Акции"),
    ]
    pagetype = models.PositiveSmallIntegerField(
        "Странца", choices=PAGE_CHOICE, blank=False, default=1
    )
    previev = models.FileField(
        upload_to="settings/%Y/%m/%d/",
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
    site = models.ManyToManyField(Site, verbose_name="Сайты", blank=True, default="1")

    def __str__(self):
        return dict(self.PAGE_CHOICE).get(self.pagetype, "Неизвестная страница")

    class Meta:
        verbose_name = "Сео страницы"
        verbose_name_plural = "Сео страниц"


class ExtendedSite(models.Model):
    templates = models.CharField("Шаблон", blank=False, default="home", max_length=500)
    site = models.OneToOneField(Site, on_delete=models.CASCADE, related_name="extended")

    def __str__(self):
        return f"Дополнения для {self.site.domain}"

    class Meta:
        verbose_name = "Шаблон"
        verbose_name_plural = "Шаблоны"


class SettingsGlobale(models.Model):
    """Настройки сайта"""

    logo = models.FileField(
        "Логотип",
        upload_to="settings/%Y/%m/%d/",
        default="default/logo.png",
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
        default="default/logo.png",
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
        default="default/logo.png",
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
        default="default/logo.png",
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
        default="default/logo.png",
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
        default="default/logo.png",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    favicon = models.FileField(
        "Фавикон",
        upload_to="settings/%Y/%m/%d/",
        default="default/d.png",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    paymentmetod = models.FileField(
        "Методы оплаты",
        upload_to="settings/%Y/%m/%d/",
        default="default/oplata.webp",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    name = models.CharField(
        "Название", max_length=500, blank=True, null=True, default="Название сайта"
    )
    content = models.CharField(
        "Копирайт", max_length=500, blank=True, null=True, default="Все права защищены"
    )
    description = models.TextField(
        "Описание", blank=True, null=True, default="Описание сайта"
    )
    slogan = models.CharField(
        "Слоган", max_length=500, blank=True, null=True, default="Слоган сайта"
    )
    message_header = models.TextField(
        "Шапка сообщения письма", blank=True, null=True, default="От сервиса"
    )
    message_footer = models.TextField(
        "Подвал сообщения письма", blank=True, null=True, default="От сервиса"
    )
    yandex_metrica = models.TextField(
        "Яндекс метрика", blank=True, null=True, default="<link>"
    )
    google_analitic = models.TextField(
        "Гугл аналитика", blank=True, null=True, default="<link>"
    )
    jsontemplate = models.TextField(
        blank=True, null=True, verbose_name="Шаблон", default="[]"
    )
    email_host = models.TextField("Email Site HOST", blank=True, null=True)
    default_from_email = models.TextField("Email Site HOST", blank=True, null=True)
    email_port = models.TextField("Email Site PORT", blank=True, null=True)
    email_host_user = models.TextField("Email Site User", blank=True, null=True)
    email_host_password = models.TextField("Email Site Password", blank=True, null=True)
    email_use_tls = models.BooleanField("Use TLS", default=False, blank=True, null=True)
    email_use_ssl = models.BooleanField("Use SSL", default=False, blank=True, null=True)
    site = models.OneToOneField(Site, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Сначала сохраняем модель
        super().save(*args, **kwargs)

        # Путь к файлу, куда будем сохранять данные
        file_path = os.path.join(settings.BASE_DIR, "_media\smtp.py")

        # Сохраняем данные в текстовый файл
        with open(file_path, "w") as f:
            f.write(f"EMAIL_HOST = '{self.email_host}'\n")
            f.write(f"EMAIL_PORT = '{self.email_port}'\n")
            f.write(f"EMAIL_USE_TLS = {self.email_use_tls}\n")
            f.write(f"EMAIL_USE_SSL = {self.email_use_ssl}\n")
            f.write(f"EMAIL_HOST_USER = '{self.email_host_user}'\n")
            f.write(f"EMAIL_HOST_PASSWORD = '{self.email_host_password}'\n")
            f.write(f"DEFAULT_FROM_EMAIL = '{self.default_from_email}'\n")

    class Meta:
        verbose_name = "Настройка сайта"
        verbose_name_plural = "Настройки сайта"


class ContactPage(models.Model):
    """Настройки контакты"""

    previev = models.FileField(
        upload_to="settings/%Y/%m/%d/",
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
    jsontemplate = models.TextField(
        blank=True, null=True, verbose_name="Шаблон", default="[]"
    )
    site = models.OneToOneField(Site, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Страница контакты"
        verbose_name_plural = "Страницы контакты"


class ContactPageInformation(models.Model):
    """Настройки контактов"""

    CONTACT_CHOICE = [
        (
            "Отделения",
            [
                ("branches", "Отделения"),
            ],
        ),
        (
            "Номера телефонов",
            [
                ("phone_default", "Номер телефона по умолчанию"),
                ("phone", "Остальные номера телефонов"),
            ],
        ),
        (
            "Электронная почта",
            [
                ("email_default", "Почта по умолчанию"),
                ("email", "Остальные почты"),
            ],
        ),
        (
            "Адреса",
            [
                ("address_default", "Адрес по умолчанию"),
                ("address", "Остальные адреса"),
            ],
        ),
        (
            "Карты",
            [
                ("map_default", "Карта по умолчанию"),
                ("map", "Остальные карты"),
            ],
        ),
        (
            "Социальные сети",
            [
                ("social_default", "Социальные сети по умолчанию"),
                ("social", "Остальные социальные сети"),
            ],
        ),
        (
            "График",
            [
                ("works", "Рабочие дни"),
                ("weekend", "Выходные"),
            ],
        ),
    ]
    page_type = models.CharField("Тип", max_length=50, choices=CONTACT_CHOICE)
    image = models.FileField(
        upload_to="contact/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Изображение",
        default="default/imagegallery/imagegellery_images.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, blank=True, null=True, verbose_name="Родитель"
    )
    title_contact = models.CharField(verbose_name="Заголовок контактов", max_length=350)
    description_contact = models.CharField(
        verbose_name="Описание контактов", max_length=550
    )
    information_contact = models.CharField(
        verbose_name="Информация контактов", max_length=350
    )
    setting = models.ForeignKey(
        "SettingsGlobale",
        verbose_name="Настройки",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    contactpage = models.ForeignKey(
        "ContactPage",
        verbose_name="Страница контакты",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.title_contact

    class Meta:
        verbose_name = "Страница контакты (информация)"
        verbose_name_plural = "Страницы контакты (информация)"


class AboutPage(models.Model):
    """Страница о нас (о компании)"""

    previev = models.FileField(
        upload_to="settings/%Y/%m/%d/",
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
    setting = models.ForeignKey(
        "SettingsGlobale",
        verbose_name="Настройки",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    jsontemplate = models.TextField(
        blank=True, null=True, verbose_name="Шаблон", default="[]"
    )
    site = models.OneToOneField(Site, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Страница О нас"
        verbose_name_plural = "Страницы О нас"


class HomePage(models.Model):
    """Настройки сайта"""

    previev = models.FileField(
        upload_to="settings/%Y/%m/%d/",
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
    setting = models.ForeignKey(
        "SettingsGlobale",
        verbose_name="Настройки",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    jsontemplate = models.TextField(
        blank=True, null=True, verbose_name="Шаблон", default="[]"
    )
    site = models.OneToOneField(Site, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Главная страница"
        verbose_name_plural = "Главные страницы"


class Pages(models.Model):
    """Страницы"""

    PAGETYPE = [
        (1, "Стандартная"),
        (2, "Пользовательское соглашение"),
        (3, "Политика конфиденциальности"),
        (4, "Политика Cookie - Файлов"),
        (5, "Согласия на обработку персональных данных"),
        (6, "Партнерство"),
        (7, "Сотрудничество"),
        (8, "Доставка"),
        (9, "Оплата"),
        (10, "Возврат"),
    ]
    pagetype = models.PositiveSmallIntegerField(
        "Тип", choices=PAGETYPE, blank=False, default=1
    )
    name = models.CharField("Название", max_length=250)
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
    publishet = models.BooleanField("Опубликован", default=False)
    site = models.ManyToManyField(Site, verbose_name="Сайты")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Страница"
        verbose_name_plural = "Страницы"


class Faqs(models.Model):
    """Часто задаваемые вопросы"""

    question = models.TextField(blank=True, null=True, verbose_name="Вопрос")
    answer = models.TextField(blank=True, null=True, verbose_name="Ответ", default=" ")
    create = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    update = models.DateTimeField(auto_now=True, blank=True, null=True)
    publishet = models.BooleanField("Опубликован", default=False)
    site = models.ManyToManyField(Site, verbose_name="Сайты", blank=True, default="1")

    class Meta:
        verbose_name = "Часто задаваемые вопросы"
        verbose_name_plural = "Часто задаваемые вопрос"


class CategorysBlogs(models.Model):
    """Категории"""

    name = models.CharField(max_length=150, unique=True, verbose_name="Название")
    slug = models.SlugField(
        max_length=200, unique=True, blank=True, null=True, verbose_name="URL"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    parent = models.ForeignKey(
        "self",
        related_name="children",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Родитель",
    )
    cover = models.FileField(
        "Обложка категории",
        upload_to="category/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    icon = models.FileField(
        "Иконка категории",
        upload_to="category/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    image = models.FileField(
        "Картинка категории",
        upload_to="category/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    previev = models.FileField(
        upload_to="category/%Y/%m/%d/",
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
    publishet = models.BooleanField("Опубликован", default=False)
    site = models.ManyToManyField(Site, verbose_name="Сайты", blank=True, default="1")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория новости"
        verbose_name_plural = "Категории новости"


class TagsBlogs(models.Model):
    """Метки"""

    name = models.CharField(max_length=150, unique=True, verbose_name="Название")
    slug = models.SlugField(
        max_length=200, unique=True, blank=True, null=True, verbose_name="URL"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    cover = models.FileField(
        "Обложка метки",
        upload_to="tags/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    icon = models.FileField(
        "Иконка метки",
        upload_to="tags/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    image = models.FileField(
        "Картинка метки",
        upload_to="tags/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    previev = models.FileField(
        upload_to="tags/%Y/%m/%d/",
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
    publishet = models.BooleanField("Опубликован", default=False)
    site = models.ManyToManyField(Site, verbose_name="Сайты", blank=True, default="1")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания", blank=True, null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Дата обновления", blank=True, null=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Метка новости"
        verbose_name_plural = "Метки новости"


class Blogs(models.Model):
    """Блог"""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Авторы",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    manufacturers = models.ForeignKey(
        Manufacturers,
        verbose_name="Магазин",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    resource = models.CharField("Источник", max_length=550, blank=True, null=True)
    category = models.ManyToManyField(
        CategorysBlogs, verbose_name="Категории", blank=True
    )
    tags = models.ManyToManyField(TagsBlogs, verbose_name="Метки", blank=True)
    name = models.CharField("Название", max_length=250)
    description = RichTextField("Описание")
    data = models.DateTimeField("Дата мероприятия", blank=True, null=True)
    previev = models.FileField(
        upload_to="blogs/%Y/%m/%d/",
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
        max_length=150, verbose_name="Мета-заголовок", blank=True, null=True
    )
    metadescription = models.TextField(
        blank=True, null=True, verbose_name="Мета-описание"
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
    slug = models.SlugField(max_length=140)
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
    image = models.FileField(
        "Изображение",
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
    publishet = models.BooleanField("Опубликован", default=False)
    create = models.DateTimeField(auto_now=True, blank=True, null=True)
    site = models.ManyToManyField(Site, verbose_name="Сайты", blank=True, default="1")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("webmain:blogdetail", kwargs={"slug": self.slug})

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"


class Comments(models.Model):
    """Комментарий"""

    publishet = models.BooleanField("Опубликован", default=False)
    create = models.DateTimeField(auto_now=True, blank=True, null=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Авторы",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    first_name = models.CharField("Имя", max_length=250, blank=True, null=True)
    last_name = models.CharField("Фамилия", max_length=250, blank=True, null=True)
    email = models.CharField("email", max_length=250, blank=True, null=True)
    comment = models.TextField("Комментарий", blank=True, null=True)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.TextField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    stopwords = models.ManyToManyField(Stopwords, verbose_name="Стоп слова", blank=True)
    parent = models.ForeignKey(
        "self",
        related_name="childrencomment",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Родитель",
    )

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"


class Sponsorship(models.Model):
    """Благотворительность"""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Авторы",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    resource = models.CharField("Источник", max_length=550, blank=True, null=True)
    blogs = models.ManyToManyField(Blogs, verbose_name="Новости", blank=True)
    name = models.CharField("Название", max_length=250)
    description = RichTextField("Описание", db_index=True)
    previev = models.FileField(
        upload_to="blogs/%Y/%m/%d/",
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
        max_length=150, verbose_name="Мета-заголовок", blank=True, null=True
    )
    metadescription = models.TextField(
        blank=True, null=True, verbose_name="Мета-описание"
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
    slug = models.SlugField(max_length=140, unique=True)
    cover = models.FileField(
        "Обложка",
        upload_to="blogs/%Y/%m/%d/",
        blank=True,
        null=True,
        default="default/cover.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    image = models.FileField(
        "Изображение",
        upload_to="blogs/%Y/%m/%d/",
        blank=True,
        null=True,
        default="default/cover.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    publishet = models.BooleanField("Опубликован", default=False)
    create = models.DateTimeField(auto_now=True, blank=True, null=True)
    site = models.ManyToManyField(Site, verbose_name="Сайты", blank=True, default="1")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("webmain:sponsorship", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        self.description = strip_tags(self.description)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Благотворительность"
        verbose_name_plural = "Благотворительность"


class Gallery(models.Model):
    """Галерея"""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Авторы",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    name = models.CharField("Название", max_length=250)
    description = RichTextField("Описание", db_index=True)
    previev = models.FileField(
        upload_to="galleries/%Y/%m/%d/",
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
        max_length=150, verbose_name="Мета-заголовок", blank=True, null=True
    )
    metadescription = models.TextField(
        blank=True, null=True, verbose_name="Мета-описание"
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
    slug = models.SlugField(max_length=140, unique=True)
    cover = models.FileField(
        "Обложка",
        upload_to="galleries/%Y/%m/%d/",
        blank=True,
        null=True,
        default="default/cover.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    image = models.FileField(
        "Изображение",
        upload_to="galleries/%Y/%m/%d/",
        blank=True,
        null=True,
        default="default/cover.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    publishet = models.BooleanField("Опубликован", default=False)
    create = models.DateTimeField(auto_now=True, blank=True, null=True)
    site = models.ManyToManyField(Site, verbose_name="Сайты", blank=True, default="1")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("webmain:gallery", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        self.description = strip_tags(self.description)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Галерея"
        verbose_name_plural = "Галереи"


class GalleryMedia(models.Model):
    gallery = models.ForeignKey(
        "Gallery", on_delete=models.CASCADE, verbose_name="Галерея"
    )
    file = models.FileField(upload_to="gallery/%Y/%m/%d/gallery_file/")

    def get_file_name(self):
        return os.path.basename(self.file.name)

    class Meta:
        verbose_name = "Файл галереи"
        verbose_name_plural = "Файлы галереи"


class Service(models.Model):
    """Услуги"""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Авторы",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    name = models.CharField("Название", max_length=250)
    description = RichTextField("Описание")
    previev = models.FileField(
        upload_to="blogs/%Y/%m/%d/",
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
        max_length=150, verbose_name="Мета-заголовок", blank=True, null=True
    )
    metadescription = models.TextField(
        blank=True, null=True, verbose_name="Мета-описание"
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
    slug = models.SlugField(max_length=140, unique=True)
    cover = models.FileField(
        "Обложка",
        upload_to="services/%Y/%m/%d/",
        blank=True,
        null=True,
        default="default/cover.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    image = models.FileField(
        "Изображение",
        upload_to="services/%Y/%m/%d/",
        blank=True,
        null=True,
        default="default/cover.png",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    publishet = models.BooleanField("Опубликован", default=False)
    create = models.DateTimeField(auto_now=True, blank=True, null=True)
    site = models.ManyToManyField(Site, verbose_name="Сайты", blank=True, default="1")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("webmain:service", kwargs={"slug": self.slug})

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"


class ServiceMedia(models.Model):
    service = models.ForeignKey(
        "Service", on_delete=models.CASCADE, verbose_name="Услуга"
    )
    file = models.FileField(upload_to="ticket/%Y/%m/%d/tiket_file/")

    def get_file_name(self):
        return os.path.basename(self.file.name)

    class Meta:
        verbose_name = "Файл услуги"
        verbose_name_plural = "Файлы услуги"


class Price(models.Model):
    """Прайс"""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Авторы",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    name = models.CharField("Название", max_length=250)
    description = RichTextField("Описание", db_index=True)
    title = models.CharField(
        max_length=150, verbose_name="Мета-заголовок", blank=True, null=True
    )
    metadescription = models.TextField(
        blank=True, null=True, verbose_name="Мета-описание"
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
    slug = models.SlugField(max_length=140, unique=True)
    publishet = models.BooleanField("Опубликован", default=False)
    create = models.DateTimeField(auto_now=True, blank=True, null=True)
    site = models.ManyToManyField(Site, verbose_name="Сайты", blank=True, default="1")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("webmain:price", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        self.description = strip_tags(self.description)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Прайс"
        verbose_name_plural = "Прайс"


class PriceInfo(models.Model):
    price = models.ForeignKey("Price", on_delete=models.CASCADE, verbose_name="Прайс")
    file = models.FileField(
        upload_to="ticket/%Y/%m/%d/tiket_file/", blank=True, null=True
    )
    name = models.CharField("Название", max_length=250)
    description = RichTextField("Описание", db_index=True)
    amount = models.CharField("Цена", max_length=250)
    meaning = models.CharField("Значение", max_length=250)

    def get_file_name(self):
        return os.path.basename(self.file.name)

    class Meta:
        verbose_name = "Информация по прайсу"
        verbose_name_plural = "Информации по прайсу"

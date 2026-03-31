from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings
import os
import uuid
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from multiselectfield import MultiSelectField
from django.core.validators import FileExtensionValidator
from uuid import uuid4

from shop.models import Manufacturers
from useraccount.models import Profile


# Create your models here.
class Stopwords(models.Model):
    """Стоп слова"""

    id = models.AutoField(primary_key=True)
    name = models.CharField("Стоп слова", max_length=120)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Стоп слово"
        verbose_name_plural = "Стоп слова"


class Subscriptions(models.Model):
    """Подписки"""

    email = models.CharField(
        blank=True, verbose_name="Email", unique=True, max_length=500, null=True
    )
    create = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Подписки"
        verbose_name_plural = "Подписки"


class Applications(models.Model):
    """Заявка"""

    TYPE = [
        (1, "Заявка"),
        (2, "Покупка"),
        (3, "Партнерство"),
        (4, "Сотрудничество"),
    ]
    type = models.PositiveSmallIntegerField("Тип", choices=TYPE, blank=False, default=1)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    create = models.DateTimeField(auto_now=True, blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Пользователь",
    )
    email = models.CharField(
        blank=True, verbose_name="Email", max_length=500, null=True
    )
    phone = models.CharField(
        blank=True, verbose_name="Телефон", max_length=500, null=True
    )
    content = models.TextField(blank=True, null=True, verbose_name="Описание")
    company_name = models.CharField(
        blank=True, verbose_name="Название компании", max_length=500, null=True
    )
    company_inn = models.CharField(
        blank=True, verbose_name="ИНН организации или ИП", max_length=500, null=True
    )
    company_director = models.CharField(
        blank=True, verbose_name="ФИО директора", max_length=500, null=True
    )
    company_adress = models.CharField(
        blank=True, verbose_name="Адрес", max_length=500, null=True
    )
    company_sku = models.CharField(
        blank=True,
        verbose_name="Количество товаров SKU в вашем каталоге",
        max_length=500,
        null=True,
    )
    company_description = models.TextField(
        blank=True, null=True, verbose_name="Описание"
    )

    def __str__(self):
        return self.email if self.email else "Без email"

    class Meta:
        verbose_name = "Запрос на сотрудничество"
        verbose_name_plural = "Запросы на сотрудничество"


class Collaborations(models.Model):
    name = models.CharField(blank=True, max_length=500, null=True, verbose_name="Имя")
    email = models.CharField(
        blank=True, max_length=500, null=True, verbose_name="Электронная почта"
    )
    subject = models.CharField(
        blank=True, max_length=500, null=True, verbose_name="Обьект сотрудничества"
    )
    phone = models.CharField(
        blank=True, max_length=500, null=True, verbose_name="Номер телефона"
    )
    message = models.TextField(verbose_name="Сообщение")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"


class Ticket(models.Model):
    date = models.DateTimeField(verbose_name="Дата", auto_now_add=True)
    STATUS_CHOICES = [
        (0, "Новое"),
        (1, "Обратная связь"),
        (2, "В процессе"),
        (3, "Решенный"),
        (4, "Закрытый"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.SmallIntegerField(
        verbose_name="Статус", choices=STATUS_CHOICES, default=0
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Автор", on_delete=models.CASCADE
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="ticket_manager",
        verbose_name="Менеджер",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    themas = models.TextField("Тема")

    class Meta:
        verbose_name = "Тикет"
        verbose_name_plural = "Тикеты"
        ordering = ["date"]


class TicketComment(models.Model):
    STATUS_CHOICES = [
        (0, "Заказчик"),
        (1, "Поддержка"),
    ]
    status = models.SmallIntegerField(
        verbose_name="Статус", choices=STATUS_CHOICES, default=1, editable=False
    )
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, verbose_name="Ticket", related_name="comments"
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    content = models.TextField(verbose_name="Комментарий")
    author_comments = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Автор"
    )

    class Meta:
        verbose_name = "Комментарий тикета"
        verbose_name_plural = "Комментарии тикета"
        ordering = ["-date"]


class TicketCommentMedia(models.Model):
    comment = models.ForeignKey(
        "TicketComment", on_delete=models.CASCADE, related_name="media"
    )
    file = models.FileField(upload_to="ticket/%Y/%m/%d/tiket_file/")

    def get_file_name(self):
        return os.path.basename(self.file.name)

    class Meta:
        verbose_name = "Файл комментария тикета"
        verbose_name_plural = "Файлы комментариев тикета"


class Notificationgroups(models.Model):
    """Уведомление"""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Авторы",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="author_notification",
    )
    created_at = models.DateTimeField("Созданно", auto_now_add=True)
    publication = models.DateTimeField("Дата публикации", auto_now_add=True)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={
            "model__in": (
                "blogs",
                "pages",
                "categorysblogs",
                "tagsblogs",
            )
        },
    )
    object_id = models.CharField(
        blank=True, verbose_name="Уникальный номер", max_length=500, null=True
    )
    content_object = GenericForeignKey("content_type", "object_id")
    message = models.TextField()
    slug = models.TextField(editable=False)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name="Пользователь"
    )
    email = models.TextField(
        blank=True, verbose_name="Email", max_length=500, null=True
    )

    class Meta:
        verbose_name = "Груповое уведомление"
        verbose_name_plural = "Груповые уведомления"


class ViewPage(models.Model):
    """Просмотры"""

    create = models.DateTimeField(auto_now=True, blank=True, null=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Авторы",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    ip = models.CharField("IP Адрес", max_length=15, blank=True, null=True)
    browser = models.CharField("Браузер", max_length=150, blank=True, null=True)
    operationsistem = models.CharField(
        "Операционая система", max_length=150, blank=True, null=True
    )
    region = models.CharField("Регион", max_length=150, blank=True, null=True)
    link = models.CharField("Ссылка", max_length=150, blank=True, null=True)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.TextField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    # def save(self, *args, **kwargs):
    #     dadata = Dadata("32b0e4e3d9b0fb24499c8414a81dd9411bd8a5ac")
    #     region = dadata.iplocate(self.ip)
    #     print(self.ip)
    #     self.region = region
    #     print(region)
    #     super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Просмотр страницы"
        verbose_name_plural = "Просмотры страниц"


class ViewDayPage(models.Model):
    """Просмотры"""

    create = models.DateTimeField(auto_now=True, blank=True, null=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Авторы",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    jsoninformation = models.TextField()

    class Meta:
        verbose_name = "Просмотры за день"
        verbose_name_plural = "Просмотры за дни"

class Groups(models.Model):
    TYPE_OPTIONS = (
        ("Статистика", (
            ("statistic_generate", "Генерация"),
            ("statistic_view", "Просмотр"),
        )),
        ("Группы", (
            ("groups_list", "Список"),
            ("groups_create", "Создание"),
            ("groups_edit", "Редактирование"),
            ("groups_delete", "Удаление"),
        )),
        ("Сотрудники", (
            ("employees_list", "Список"),
            ("employees_create", "Создание"),
            ("employees_edit", "Редактирование"),
            ("employees_delete", "Удаление"),
        )),
        ("Клиенты", (
            ("clients_list", "Список"),
            ("clients_create", "Создание"),
            ("clients_edit", "Редактирование"),
            ("clients_delete", "Удаление"),
        )),
        ("База знаний", (
            ("knowledge_list", "Список"),
            ("knowledge_create", "Создание"),
            ("knowledge_edit", "Редактирование"),
            ("knowledge_delete", "Удаление"),
        )),
        ("Email", (
            ("email_send", "Отправка"),
            ("email_list", "Список"),
        )),
        ("Телефония", (
            ("telephony_list", "Список"),
            ("telephony_call", "Звонок"),
        )),
        ("Проекты", (
            ("projects_list", "Список"),
            ("projects_create", "Создание"),
            ("projects_edit", "Редактирование"),
            ("projects_delete", "Удаление"),
        )),
        ("Проделаные работы", (
            ("works_list", "Список"),
        )),
        ("График", (
            ("schedule_view", "Просмотр"),
            ("schedule_edit", "Редактирование"),
        )),
        ("Задачник", (
            ("tasks_list", "Список"),
            ("tasks_create", "Создание"),
            ("tasks_edit", "Редактирование"),
            ("tasks_delete", "Удаление"),
        )),
        ("Бухгалтерия", (
            ("accounting_view", "Просмотр"),
        )),
        ("Платежи", (
            ("payments_list", "Список"),
            ("payments_create", "Создание"),
        )),
        ("Запросы", (
            ("requests_list", "Список"),
        )),
        ("Хоз.часть", (
            ("admin_part_view", "Просмотр"),
        )),
        ("Урок", (
            ("lesson_list", "Список"),
        )),
        ("Обучение", (
            ("training_list", "Список"),
        )),
        ("Вакансии", (
            ("vacancies_list", "Список"),
            ("vacancies_create", "Создание"),
            ("vacancies_edit", "Редактирование"),
            ("vacancies_delete", "Удаление"),
        )),
        ("Заявки", (
            ("applications_list", "Список"),
            ("applications_create", "Создание"),
        )),
        ("Склады (Магазины)", (
            ("storages_list", "Список"),
            ("storages_create", "Создание"),
            ("storages_edit", "Редактирование"),
            ("storages_delete", "Удаление"),
        )),
        ("Компании", (
            ("companies_list", "Список"),
            ("companies_create", "Создание"),
        )),
        ("Товары", (
            ("products_list", "Список"),
            ("products_create", "Создание"),
            ("products_edit", "Редактирование"),
            ("products_delete", "Удаление"),
        )),
        ("Категории", (
            ("categories_list", "Список"),
            ("categories_create", "Создание"),
        )),
        ("Покупки", (
            ("purchases_list", "Список"),
        )),
        ("Жалобы", (
            ("complaints_list", "Список"),
        )),
        ("Отзывы", (
            ("reviews_list", "Список"),
        )),
        ("Комментарии", (
            ("comments_list", "Список"),
        )),
        ("Вопросы", (
            ("questions_list", "Список"),
        )),
        ("Вариации", (
            ("variations_list", "Список"),
        )),
        ("Валюта", (
            ("currency_list", "Список"),
        )),
        ("Поддержка", (
            ("support_list", "Список"),
        )),
        ("Тикеты", (
            ("tickets_list", "Список"),
        )),
        ("Обращение", (
            ("requests_view", "Просмотр"),
        )),
        ("Домены", (
            ("domains_list", "Список"),
            ("domains_create", "Создание"),
        )),
        ("Програма лояльности", (
            ("loyalty_list", "Список"),
        )),
        ("Уведомления", (
            ("notifications_list", "Список"),
        )),
        ("Языки", (
            ("languages_list", "Список"),
        )),
        ("Интеграции", (
            ("integrations_list", "Список"),
        )),
        ("Блог (Новости)", (
            ("blog_list", "Список"),
        )),
        ("Страницы", (
            ("pages_list", "Список"),
        )),
        ("Благотворительность", (
            ("charity_list", "Список"),
        )),
        ("Галерея", (
            ("gallery_list", "Список"),
        )),
        ("Услуги", (
            ("services_list", "Список"),
        )),
        ("Прайс", (
            ("price_list", "Список"),
        )),
        ("ЧаВо", (
            ("faq_list", "Список"),
        )),
        ("Документация", (
            ("docs_list", "Список"),
        )),
        ("Личные", (
            ("personal_view", "Просмотр"),
        )),
        ("Профиль", (
            ("profile_view", "Просмотр"),
        )),
        ("Начисления", (
            ("charges_list", "Список"),
        )),
    )

    types = MultiSelectField(
        choices=TYPE_OPTIONS,
        blank=True,
        verbose_name="Доступ",
        default=list,
        null=True,
        max_length=255,
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(editable=False)
    name = models.CharField(max_length=150, verbose_name="Название")
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователи",
        blank=True,
        related_name="groupsuser",
    )


    def get_types_display(self):
        return ", ".join(dict(self.TYPE_OPTIONS).get(type_id) for type_id in self.types)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

class AggregatedExpense(models.Model):
    store = models.ForeignKey(Manufacturers, on_delete=models.CASCADE, verbose_name='Магазин')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    data = models.DateTimeField(verbose_name='Дата', blank=True, null=True)
    revenue_by_products = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Выручка по товарам')
    expenses_by_products = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Расходы по товарам')
    expenses_by_store = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Расходы магазина')
    expenses_by_employee = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Расходы по Сотрудникам')
    income = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Доходы')

    def __str__(self):
        return f"AggregatedExpense #{self.id} - {self.store.name} ({self.created_at.date()})"



class ReklamBanner(models.Model):
    TYPE_OPTIONS = (
        (
            "В категории",
            (
                (
                    "categorys_gorizont",
                    "Горизонтальные",
                ),
                ("categorys_vertikal", "Вертикальные"),
            ),
        ),
        (
            "Каталог",
            (
                (
                    "catalog_gorizont",
                    "Горизонтальные",
                ),
                ("catalog_vertikal", "Вертикальные"),
            ),
        ),
    )
    types = MultiSelectField(
        choices=TYPE_OPTIONS,
        blank=True,
        verbose_name="Типы",
        default=list,
        null=True,
        max_length=255,  # Добавьте это, чтобы предотвратить ошибку с длиной
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.FileField(
        "Изображение",
        upload_to="product/%Y/%m/%d/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
            )
        ],
    )
    title = models.CharField(max_length=150, verbose_name="Заголовок")
    content = models.TextField(blank=True, null=True, verbose_name="Описание")
    link_name = models.CharField(max_length=150, verbose_name="Название ссылки")
    link = models.CharField(max_length=150, verbose_name="Ссылка")
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={
            "model__in": (
                "blogs",
                "categories",
                "pages",
                "categorysblogs",
                "tagsblogs",
            )
        },
        blank=True,
        null=True,
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = "Рекламный баннер"
        verbose_name_plural = "Рекламные баннеры"


class Asset(models.Model):
    """
    Основная модель имущества компании.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField("Название", max_length=255)
    inventory_number = models.CharField(
        "Инвентарный номер", max_length=100, unique=True
    )
    description = models.TextField("Описание", blank=True)
    purchase_date = models.DateField("Дата покупки", null=True, blank=True)
    warranty_expiration = models.DateField("Окончание гарантии", null=True, blank=True)
    location = models.CharField("Расположение", max_length=255, blank=True)
    responsible_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Ответственный сотрудник",
    )
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.inventory_number})"

    class Meta:
        verbose_name = "Имущество компании"
        verbose_name_plural = "Имущества компании"


class Maintenance(models.Model):
    """
    Запись о техническом обслуживании.
    """

    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="maintenance_records"
    )
    date = models.DateField("Дата обслуживания")
    performed_by = models.CharField("Выполнил", max_length=255)
    description = models.TextField("Описание работ")
    next_due_date = models.DateField("Следующее ТО", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ТО для {self.asset.name} от {self.date}"

    class Meta:
        verbose_name = "Техническое обслуживание"
        verbose_name_plural = "Технические обслуживания"


class AssetUsage(models.Model):
    """
    История использования имущества: кто, когда брал и когда вернул.
    """

    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="usage_records"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Пользователь",
    )
    taken_at = models.DateTimeField("Дата выдачи")
    returned_at = models.DateTimeField("Дата возврата", null=True, blank=True)
    purpose = models.CharField("Цель использования", max_length=255, blank=True)
    is_active = models.BooleanField("Активен", default=True)

    def is_returned(self):
        return self.returned_at is not None

    def __str__(self):
        return f"{self.asset.name} - {self.user} [{self.taken_at} - {self.returned_at or 'ещё не вернул'}]"

    class Meta:
        verbose_name = "История использования"
        verbose_name_plural = "Истории использований"


User = get_user_model()


class EmailTemplate(models.Model):
    """Модель для шаблонов email"""
    CATEGORY_CHOICES = [
        ('registration', 'Регистрация'),
        ('password_reset', 'Восстановление пароля'),
        ('order', 'Заказы'),
        ('payment', 'Платежи'),
        ('newsletter', 'Рассылка'),
        ('notification', 'Уведомления'),
        ('promotion', 'Акции'),
        ('support', 'Поддержка'),
    ]

    name = models.CharField(max_length=200, verbose_name="Название шаблона")
    subject = models.CharField(max_length=300, verbose_name="Тема письма")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Уникальный идентификатор")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name="Категория")
    content = models.TextField(verbose_name="Содержание письма (HTML)")
    plain_content = models.TextField(verbose_name="Текстовая версия", blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    variables = models.JSONField(default=list, blank=True, verbose_name="Доступные переменные",
                                 help_text="Список доступных переменных для шаблона")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Шаблон email"
        verbose_name_plural = "Шаблоны email"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.get_category_display()}"


class EmailLog(models.Model):
    """Лог отправленных писем"""
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('sent', 'Отправлено'),
        ('failed', 'Ошибка'),
        ('opened', 'Открыто'),
        ('clicked', 'Кликнут'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Получатель")
    recipient_email = models.EmailField(verbose_name="Email получателя")
    recipient_name = models.CharField(max_length=200, blank=True, verbose_name="Имя получателя")
    subject = models.CharField(max_length=500, verbose_name="Тема")
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Шаблон")
    content = models.TextField(verbose_name="Содержание")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    error_message = models.TextField(blank=True, verbose_name="Ошибка")

    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Время отправки")
    opened_at = models.DateTimeField(null=True, blank=True, verbose_name="Время открытия")
    clicked_at = models.DateTimeField(null=True, blank=True, verbose_name="Время клика")

    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP адрес")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Лог email"
        verbose_name_plural = "Логи email"
        ordering = ['-created_at']

    def __str__(self):
        return f"Email to {self.recipient_email} - {self.get_status_display()}"


class EmailAttachment(models.Model):
    """Модель для вложений"""
    email_log = models.ForeignKey(EmailLog, on_delete=models.CASCADE, related_name='attachments', verbose_name="Email")
    file = models.FileField(upload_to='email_attachments/%Y/%m/%d/', verbose_name="Файл")
    filename = models.CharField(max_length=255, verbose_name="Имя файла")
    file_size = models.IntegerField(verbose_name="Размер файла", help_text="в байтах")
    content_type = models.CharField(max_length=100, verbose_name="Тип контента")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Вложение"
        verbose_name_plural = "Вложения"

    def __str__(self):
        return self.filename


class EmailQueue(models.Model):
    """Очередь для отложенной отправки"""
    PRIORITY_CHOICES = [
        (1, 'Низкий'),
        (2, 'Средний'),
        (3, 'Высокий'),
        (4, 'Срочный'),
    ]

    recipient_email = models.EmailField(verbose_name="Email получателя")
    recipient_name = models.CharField(max_length=200, blank=True, verbose_name="Имя получателя")
    subject = models.CharField(max_length=500, verbose_name="Тема")
    content = models.TextField(verbose_name="Содержание")
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2, verbose_name="Приоритет")
    scheduled_for = models.DateTimeField(default=timezone.now, verbose_name="Запланировано на")

    is_sent = models.BooleanField(default=False, verbose_name="Отправлено")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Отправлено в")
    attempts = models.IntegerField(default=0, verbose_name="Попытки отправки")
    error = models.TextField(blank=True, verbose_name="Ошибка")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Очередь email"
        verbose_name_plural = "Очередь email"
        ordering = ['-priority', 'scheduled_for']

    def __str__(self):
        return f"Queue: {self.recipient_email} - {self.subject[:50]}"


class PhoneNumber(models.Model):
    """Модель телефонных номеров"""
    STATUS_CHOICES = [
        ('active', 'Активен'),
        ('inactive', 'Неактивен'),
        ('blocked', 'Заблокирован'),
        ('pending', 'На проверке'),
    ]

    number = models.CharField(max_length=20, unique=True, verbose_name="Номер телефона")
    extension = models.CharField(max_length=10, blank=True, verbose_name="Внутренний номер")
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='phone_numbers', verbose_name="Владелец")
    department = models.CharField(max_length=100, blank=True, verbose_name="Отдел")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Статус")

    # Технические параметры
    sip_login = models.CharField(max_length=100, blank=True, verbose_name="SIP логин")
    sip_password = models.CharField(max_length=100, blank=True, verbose_name="SIP пароль")
    sip_server = models.CharField(max_length=200, blank=True, verbose_name="SIP сервер")

    is_primary = models.BooleanField(default=False, verbose_name="Основной номер")
    is_ivr = models.BooleanField(default=False, verbose_name="IVR номер")
    ivr_menu = models.JSONField(default=dict, blank=True, verbose_name="IVR меню",
                                help_text='{"1": "ext:101", "2": "group:support"}')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Телефонный номер"
        verbose_name_plural = "Телефонные номера"
        ordering = ['number']

    def __str__(self):
        return f"{self.number} ({self.owner or 'Не назначен'})"


class CallRecord(models.Model):
    """Модель записи звонков"""
    DIRECTION_CHOICES = [
        ('inbound', 'Входящий'),
        ('outbound', 'Исходящий'),
        ('internal', 'Внутренний'),
    ]

    STATUS_CHOICES = [
        ('answered', 'Отвечен'),
        ('missed', 'Пропущен'),
        ('busy', 'Занято'),
        ('failed', 'Ошибка'),
        ('voicemail', 'Голосовая почта'),
    ]

    # Информация о звонке
    call_id = models.CharField(max_length=100, unique=True, verbose_name="ID звонка")
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, verbose_name="Направление")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='answered', verbose_name="Статус")

    # Номера
    caller_number = models.CharField(max_length=20, verbose_name="Номер звонящего")
    caller_name = models.CharField(max_length=200, blank=True, verbose_name="Имя звонящего")
    callee_number = models.CharField(max_length=20, verbose_name="Номер получателя")
    callee_name = models.CharField(max_length=200, blank=True, verbose_name="Имя получателя")

    # Участники
    caller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='outgoing_calls', verbose_name="Звонящий")
    callee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='incoming_calls', verbose_name="Получатель")

    # Время и длительность
    start_time = models.DateTimeField(verbose_name="Время начала")
    answer_time = models.DateTimeField(null=True, blank=True, verbose_name="Время ответа")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="Время окончания")
    duration = models.IntegerField(default=0, verbose_name="Длительность (сек)")
    wait_duration = models.IntegerField(default=0, verbose_name="Ожидание ответа (сек)")

    # Запись разговора
    recording_url = models.URLField(max_length=500, blank=True, verbose_name="URL записи")
    recording_file = models.FileField(upload_to='call_recordings/%Y/%m/%d/', blank=True,
                                      verbose_name="Файл записи")
    recording_duration = models.IntegerField(default=0, verbose_name="Длительность записи (сек)")

    # Дополнительная информация
    cost = models.DecimalField(max_digits=10, decimal_places=4, default=0, verbose_name="Стоимость")
    notes = models.TextField(blank=True, verbose_name="Примечания")
    tags = models.JSONField(default=list, blank=True, verbose_name="Теги")

    # Техническая информация
    sip_call_id = models.CharField(max_length=200, blank=True, verbose_name="SIP Call ID")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP адрес")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Запись звонка"
        verbose_name_plural = "Записи звонков"
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['caller_number', 'callee_number']),
            models.Index(fields=['start_time']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.get_direction_display()}: {self.caller_number} -> {self.callee_number}"

    def get_duration_formatted(self):
        """Форматированная длительность"""
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes:02d}:{seconds:02d}"

    def get_wait_formatted(self):
        """Форматированное ожидание"""
        minutes = self.wait_duration // 60
        seconds = self.wait_duration % 60
        return f"{minutes:02d}:{seconds:02d}"


class CallQueue(models.Model):
    """Модель очереди звонков"""
    name = models.CharField(max_length=100, verbose_name="Название очереди")
    extension = models.CharField(max_length=20, unique=True, verbose_name="Внутренний номер")

    # Стратегия распределения
    STRATEGY_CHOICES = [
        ('ringall', 'Звонок всем'),
        ('leastrecent', 'Наименее недавний'),
        ('fewestcalls', 'Наименьшее кол-во звонков'),
        ('random', 'Случайный'),
        ('roundrobin', 'По кругу'),
    ]

    strategy = models.CharField(max_length=20, choices=STRATEGY_CHOICES, default='ringall',
                                verbose_name="Стратегия")

    # Настройки
    timeout = models.IntegerField(default=20, verbose_name="Таймаут (сек)")
    max_wait_time = models.IntegerField(default=300, verbose_name="Макс. время ожидания (сек)")
    music_on_hold = models.FileField(upload_to='queue_music/', blank=True, verbose_name="Музыка ожидания")

    # Участники
    members = models.ManyToManyField(User, related_name='queues', verbose_name="Операторы")

    # Статистика
    total_calls = models.IntegerField(default=0, verbose_name="Всего звонков")
    answered_calls = models.IntegerField(default=0, verbose_name="Отвеченные")
    missed_calls = models.IntegerField(default=0, verbose_name="Пропущенные")
    avg_wait_time = models.FloatField(default=0, verbose_name="Ср. время ожидания")

    is_active = models.BooleanField(default=True, verbose_name="Активна")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Очередь звонков"
        verbose_name_plural = "Очереди звонков"

    def __str__(self):
        return f"{self.name} ({self.extension})"


class VoiceMenu(models.Model):
    """Модель голосового меню (IVR)"""
    name = models.CharField(max_length=100, verbose_name="Название")
    extension = models.CharField(max_length=20, unique=True, verbose_name="Внутренний номер")

    # Настройки
    greeting_message = models.TextField(verbose_name="Приветственное сообщение")
    greeting_audio = models.FileField(upload_to='ivr_greetings/', blank=True, verbose_name="Аудио приветствие")

    # Меню
    menu_items = models.JSONField(default=dict, verbose_name="Пункты меню",
                                  help_text='{"1": {"action": "transfer", "target": "101"}, "2": {"action": "queue", "target": "support"}}')

    timeout = models.IntegerField(default=5, verbose_name="Таймаут (сек)")
    max_retries = models.IntegerField(default=3, verbose_name="Макс. попыток")
    invalid_action = models.JSONField(default=dict, verbose_name="Действие при ошибке")

    is_active = models.BooleanField(default=True, verbose_name="Активно")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Голосовое меню"
        verbose_name_plural = "Голосовые меню"

    def __str__(self):
        return f"{self.name} ({self.extension})"


class CallRecording(models.Model):
    """Модель записей разговоров"""
    call = models.OneToOneField(CallRecord, on_delete=models.CASCADE, related_name='recording_detail',
                                verbose_name="Звонок")

    # Файлы записи
    audio_file = models.FileField(upload_to='call_recordings/%Y/%m/%d/', verbose_name="Аудио файл")
    file_size = models.IntegerField(default=0, verbose_name="Размер файла (байт)")
    file_format = models.CharField(max_length=10, default='mp3', verbose_name="Формат")

    # Транскрипция
    transcript = models.TextField(blank=True, verbose_name="Транскрипция")
    transcript_status = models.CharField(max_length=20, default='pending',
                                         choices=[('pending', 'В обработке'), ('completed', 'Готово'),
                                                  ('failed', 'Ошибка')],
                                         verbose_name="Статус транскрипции")

    # Аналитика разговора
    sentiment_score = models.FloatField(null=True, blank=True, verbose_name="Тон разговора (-1 до 1)")
    keywords = models.JSONField(default=list, blank=True, verbose_name="Ключевые слова")
    talk_ratio = models.JSONField(default=dict, blank=True, verbose_name="Соотношение речи",
                                  help_text='{"caller": 45, "callee": 55}')

    is_downloaded = models.BooleanField(default=False, verbose_name="Скачано")
    download_count = models.IntegerField(default=0, verbose_name="Количество скачиваний")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Запись разговора"
        verbose_name_plural = "Записи разговоров"

    def __str__(self):
        return f"Recording for call {self.call.id}"


class CallSettings(models.Model):
    """Модель настроек телефонии"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='phone_settings',
                                verbose_name="Пользователь")

    # Основные настройки
    extension = models.CharField(max_length=20, blank=True, verbose_name="Внутренний номер")
    mobile_forward = models.CharField(max_length=20, blank=True, verbose_name="Переадресация на мобильный")
    email_forward = models.EmailField(blank=True, verbose_name="Email для уведомлений")

    # Настройки уведомлений
    notify_on_call = models.BooleanField(default=True, verbose_name="Уведомлять о звонках")
    notify_on_missed = models.BooleanField(default=True, verbose_name="Уведомлять о пропущенных")
    notify_by_email = models.BooleanField(default=True, verbose_name="Уведомлять по email")
    notify_by_sms = models.BooleanField(default=False, verbose_name="Уведомлять по SMS")

    # Настройки записи
    auto_record = models.BooleanField(default=True, verbose_name="Автоматическая запись")
    record_outbound = models.BooleanField(default=True, verbose_name="Записывать исходящие")
    record_inbound = models.BooleanField(default=True, verbose_name="Записывать входящие")

    # Рабочее время
    work_start = models.TimeField(default='09:00', verbose_name="Начало работы")
    work_end = models.TimeField(default='18:00', verbose_name="Конец работы")
    work_days = models.JSONField(default=list, verbose_name="Рабочие дни",
                                 help_text='[1,2,3,4,5] - Пн-Пт')

    # Статус
    is_online = models.BooleanField(default=True, verbose_name="В сети")
    dnd_mode = models.BooleanField(default=False, verbose_name="Не беспокоить")
    away_message = models.TextField(blank=True, verbose_name="Сообщение отсутствия")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Настройки телефонии"
        verbose_name_plural = "Настройки телефонии"

    def __str__(self):
        return f"Settings for {self.user.username}"


class CallAnalytics(models.Model):
    """Модель аналитики звонков"""
    date = models.DateField(verbose_name="Дата")

    # Общая статистика
    total_calls = models.IntegerField(default=0, verbose_name="Всего звонков")
    answered_calls = models.IntegerField(default=0, verbose_name="Отвеченные")
    missed_calls = models.IntegerField(default=0, verbose_name="Пропущенные")
    inbound_calls = models.IntegerField(default=0, verbose_name="Входящие")
    outbound_calls = models.IntegerField(default=0, verbose_name="Исходящие")

    # Временные показатели
    total_duration = models.IntegerField(default=0, verbose_name="Общая длительность (сек)")
    avg_duration = models.FloatField(default=0, verbose_name="Средняя длительность (сек)")
    avg_wait_time = models.FloatField(default=0, verbose_name="Среднее ожидание (сек)")
    avg_response_time = models.FloatField(default=0, verbose_name="Среднее время ответа (сек)")

    # Качество обслуживания
    answered_rate = models.FloatField(default=0, verbose_name="Процент отвеченных")
    missed_rate = models.FloatField(default=0, verbose_name="Процент пропущенных")
    satisfaction_rate = models.FloatField(default=0, verbose_name="Удовлетворенность")

    # По операторам
    operator_stats = models.JSONField(default=dict, verbose_name="Статистика операторов")

    # По очередям
    queue_stats = models.JSONField(default=dict, verbose_name="Статистика очередей")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Аналитика звонков"
        verbose_name_plural = "Аналитика звонков"
        unique_together = ['date']
        ordering = ['-date']

    def __str__(self):
        return f"Analytics for {self.date}"


class IntegrationService(models.Model):
    """Базовая модель для всех интеграций"""
    SERVICE_TYPES = [
        ('marketplace', 'Маркетплейс'),
        ('payment', 'Платежная система'),
        ('delivery', 'Служба доставки'),
        ('messenger', 'Мессенджер'),
        ('additional', 'Дополнительный сервис'),
    ]

    name = models.CharField(max_length=100, verbose_name="Название сервиса")
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES, verbose_name="Тип сервиса")
    code = models.SlugField(max_length=50, unique=True, verbose_name="Код сервиса")
    logo = models.ImageField(upload_to='integrations/logos/', blank=True, verbose_name="Логотип")

    # Настройки подключения
    api_url = models.URLField(blank=True, verbose_name="API URL")
    api_key = models.CharField(max_length=500, blank=True, verbose_name="API ключ")
    api_secret = models.CharField(max_length=500, blank=True, verbose_name="API секрет")
    webhook_url = models.URLField(blank=True, verbose_name="Webhook URL")

    # Дополнительные настройки
    settings = models.JSONField(default=dict, blank=True, verbose_name="Дополнительные настройки")

    is_active = models.BooleanField(default=False, verbose_name="Активен")
    last_sync = models.DateTimeField(null=True, blank=True, verbose_name="Последняя синхронизация")
    sync_status = models.CharField(max_length=20, default='pending',
                                   choices=[('pending', 'Ожидает'), ('success', 'Успешно'), ('error', 'Ошибка')],
                                   verbose_name="Статус синхронизации")
    error_message = models.TextField(blank=True, verbose_name="Сообщение об ошибке")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Интеграция"
        verbose_name_plural = "Интеграции"
        ordering = ['service_type', 'name']

    def __str__(self):
        return f"{self.get_service_type_display()}: {self.name}"


class IntegrationLog(models.Model):
    """Логи работы интеграций"""
    OPERATION_TYPES = [
        ('sync_products', 'Синхронизация товаров'),
        ('sync_orders', 'Синхронизация заказов'),
        ('sync_stocks', 'Синхронизация остатков'),
        ('sync_prices', 'Синхронизация цен'),
        ('payment', 'Платеж'),
        ('delivery', 'Доставка'),
        ('webhook', 'Webhook'),
        ('error', 'Ошибка'),
    ]

    integration = models.ForeignKey(IntegrationService, on_delete=models.CASCADE,
                                    related_name='logs', verbose_name="Интеграция")
    operation = models.CharField(max_length=50, choices=OPERATION_TYPES, verbose_name="Операция")
    status = models.CharField(max_length=20,
                              choices=[('success', 'Успех'), ('error', 'Ошибка'), ('pending', 'В процессе')],
                              default='pending', verbose_name="Статус")

    request_data = models.JSONField(default=dict, blank=True, verbose_name="Данные запроса")
    response_data = models.JSONField(default=dict, blank=True, verbose_name="Данные ответа")
    error_message = models.TextField(blank=True, verbose_name="Сообщение об ошибке")

    duration = models.FloatField(default=0, verbose_name="Длительность (сек)")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Лог интеграции"
        verbose_name_plural = "Логи интеграций"
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.integration.name} - {self.get_operation_display()} - {self.get_status_display()}"

    def get_duration_formatted(self):
        """Форматированная длительность"""
        if self.duration < 60:
            return f"{self.duration:.2f} сек"
        else:
            return f"{self.duration / 60:.2f} мин"


# ========== Маркетплейсы ==========

class MarketplaceProduct(models.Model):
    """Модель товара на маркетплейсе"""
    marketplace = models.ForeignKey(IntegrationService, on_delete=models.CASCADE,
                                    limit_choices_to={'service_type': 'marketplace'},
                                    related_name='marketplace_products',
                                    verbose_name="Маркетплейс")

    # Связь с внутренним товаром (используем строковую ссылку, так как модель Product может быть в другом приложении)
    product_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID внутреннего товара")

    # Данные маркетплейса
    marketplace_product_id = models.CharField(max_length=100, verbose_name="ID товара на маркетплейсе")
    marketplace_sku = models.CharField(max_length=100, verbose_name="SKU на маркетплейсе", blank=True)
    marketplace_url = models.URLField(blank=True, verbose_name="Ссылка на товар")

    # Характеристики
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Цена")
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Старая цена")
    stock = models.IntegerField(default=0, verbose_name="Остаток")

    # Статусы
    status = models.CharField(max_length=50, default='active',
                              choices=[('active', 'Активен'), ('inactive', 'Неактивен'), ('archived', 'Архивирован')],
                              verbose_name="Статус")

    # Синхронизация
    last_sync = models.DateTimeField(auto_now=True, verbose_name="Последняя синхронизация")
    sync_errors = models.TextField(blank=True, verbose_name="Ошибки синхронизации")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Товар маркетплейса"
        verbose_name_plural = "Товары маркетплейсов"
        unique_together = ['marketplace', 'marketplace_product_id']

    def __str__(self):
        return f"{self.marketplace.name}: {self.marketplace_sku or self.marketplace_product_id}"


class MarketplaceOrder(models.Model):
    """Модель заказа на маркетплейсе"""
    marketplace = models.ForeignKey(IntegrationService, on_delete=models.CASCADE,
                                    limit_choices_to={'service_type': 'marketplace'},
                                    related_name='marketplace_orders',
                                    verbose_name="Маркетплейс")

    # Связь с внутренним заказом
    order_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID внутреннего заказа")

    # Данные маркетплейса
    marketplace_order_id = models.CharField(max_length=100, verbose_name="ID заказа на маркетплейсе")
    marketplace_status = models.CharField(max_length=50, verbose_name="Статус на маркетплейсе")

    # Данные заказа
    order_date = models.DateTimeField(verbose_name="Дата заказа")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма заказа")
    delivery_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Стоимость доставки")

    # Информация о покупателе
    customer_name = models.CharField(max_length=200, blank=True, verbose_name="Имя покупателя")
    customer_phone = models.CharField(max_length=50, blank=True, verbose_name="Телефон")
    customer_email = models.EmailField(blank=True, verbose_name="Email")
    delivery_address = models.TextField(blank=True, verbose_name="Адрес доставки")

    # Товары в заказе
    items = models.JSONField(default=list, verbose_name="Товары в заказе")

    # Статус синхронизации
    sync_status = models.CharField(max_length=20, default='pending',
                                   choices=[('pending', 'Ожидает'), ('synced', 'Синхронизирован'), ('error', 'Ошибка')],
                                   verbose_name="Статус синхронизации")
    sync_errors = models.TextField(blank=True, verbose_name="Ошибки синхронизации")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Заказ маркетплейса"
        verbose_name_plural = "Заказы маркетплейсов"
        unique_together = ['marketplace', 'marketplace_order_id']

    def __str__(self):
        return f"{self.marketplace.name}: {self.marketplace_order_id}"


# ========== Платежные системы ==========

class PaymentIntegration(models.Model):
    """Модель платежной интеграции"""
    PAYMENT_TYPES = [
        ('bank', 'Банк'),
        ('e_wallet', 'Электронный кошелек'),
        ('crypto', 'Криптовалюта'),
    ]

    integration = models.OneToOneField(IntegrationService, on_delete=models.CASCADE,
                                       limit_choices_to={'service_type': 'payment'},
                                       related_name='payment_settings', verbose_name="Интеграция")

    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='bank', verbose_name="Тип платежа")

    # Настройки
    merchant_id = models.CharField(max_length=100, blank=True, verbose_name="ID мерчанта")
    secret_key = models.CharField(max_length=500, blank=True, verbose_name="Секретный ключ")
    public_key = models.TextField(blank=True, verbose_name="Публичный ключ")

    # Комиссии
    commission_percent = models.FloatField(default=0, verbose_name="Комиссия (%)")
    commission_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                           verbose_name="Фиксированная комиссия")

    # Настройки обработки
    auto_confirm = models.BooleanField(default=True, verbose_name="Автоподтверждение")
    success_url = models.URLField(blank=True, verbose_name="URL успешной оплаты")
    fail_url = models.URLField(blank=True, verbose_name="URL ошибки оплаты")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Настройки платежной системы"
        verbose_name_plural = "Настройки платежных систем"

    def __str__(self):
        return f"{self.integration.name} - {self.get_payment_type_display()}"


class PaymentTransaction(models.Model):
    """Модель платежной транзакции"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('processing', 'В обработке'),
        ('success', 'Успешно'),
        ('failed', 'Ошибка'),
        ('refunded', 'Возвращен'),
        ('cancelled', 'Отменен'),
    ]

    payment = models.ForeignKey(IntegrationService, on_delete=models.CASCADE,
                                limit_choices_to={'service_type': 'payment'},
                                related_name='payment_transactions',
                                verbose_name="Платежная система")

    # Связь с заказом
    order_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID заказа")

    # Данные транзакции
    transaction_id = models.CharField(max_length=100, unique=True, verbose_name="ID транзакции")
    external_id = models.CharField(max_length=100, blank=True, verbose_name="ID во внешней системе")

    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    currency = models.CharField(max_length=3, default='RUB', verbose_name="Валюта")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")

    # Данные плательщика
    payer_name = models.CharField(max_length=200, blank=True, verbose_name="Имя плательщика")
    payer_email = models.EmailField(blank=True, verbose_name="Email плательщика")
    payer_phone = models.CharField(max_length=50, blank=True, verbose_name="Телефон")

    # Дополнительные данные
    payment_data = models.JSONField(default=dict, blank=True, verbose_name="Данные платежа")
    callback_data = models.JSONField(default=dict, blank=True, verbose_name="Данные callback")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата оплаты")

    class Meta:
        verbose_name = "Платежная транзакция"
        verbose_name_plural = "Платежные транзакции"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_id} - {self.amount} {self.currency} - {self.get_status_display()}"


# ========== Службы доставки ==========

class DeliveryIntegration(models.Model):
    """Модель интеграции со службой доставки"""
    integration = models.OneToOneField(IntegrationService, on_delete=models.CASCADE,
                                       limit_choices_to={'service_type': 'delivery'},
                                       related_name='delivery_settings', verbose_name="Интеграция")

    # Настройки
    account_number = models.CharField(max_length=100, blank=True, verbose_name="Номер аккаунта")
    warehouse_id = models.CharField(max_length=100, blank=True, verbose_name="ID склада")

    # Настройки доставки
    default_delivery_type = models.CharField(max_length=50, blank=True, verbose_name="Тип доставки по умолчанию")
    auto_create_order = models.BooleanField(default=False, verbose_name="Автосоздание заказа")
    print_label = models.BooleanField(default=True, verbose_name="Печать этикеток")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Настройки доставки"
        verbose_name_plural = "Настройки доставки"

    def __str__(self):
        return f"{self.integration.name}"


class DeliveryOrder(models.Model):
    """Модель заказа доставки"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('processing', 'В обработке'),
        ('accepted', 'Принят'),
        ('picking', 'Сборка'),
        ('delivering', 'Доставка'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
        ('error', 'Ошибка'),
    ]

    delivery = models.ForeignKey(IntegrationService, on_delete=models.CASCADE,
                                 limit_choices_to={'service_type': 'delivery'},
                                 related_name='delivery_orders',
                                 verbose_name="Служба доставки")

    # Связь с заказом
    order_id = models.PositiveIntegerField(verbose_name="ID заказа")

    # Данные доставки
    delivery_order_id = models.CharField(max_length=100, blank=True, verbose_name="ID доставки")
    tracking_number = models.CharField(max_length=100, blank=True, verbose_name="Трек-номер")
    tracking_url = models.URLField(blank=True, verbose_name="URL отслеживания")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")

    # Информация о доставке
    delivery_type = models.CharField(max_length=50, verbose_name="Тип доставки")
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Стоимость")
    estimated_delivery = models.DateField(null=True, blank=True, verbose_name="Ожидаемая дата")
    actual_delivery = models.DateField(null=True, blank=True, verbose_name="Фактическая дата")

    # Адрес
    recipient_name = models.CharField(max_length=200, verbose_name="Имя получателя")
    recipient_phone = models.CharField(max_length=50, verbose_name="Телефон")
    recipient_address = models.TextField(verbose_name="Адрес")

    # Этикетка
    label_url = models.URLField(blank=True, verbose_name="URL этикетки")
    label_file = models.FileField(upload_to='delivery_labels/%Y/%m/', blank=True, verbose_name="Файл этикетки")

    # Вес и габариты
    weight = models.FloatField(default=0, verbose_name="Вес (кг)")
    length = models.FloatField(default=0, verbose_name="Длина (см)")
    width = models.FloatField(default=0, verbose_name="Ширина (см)")
    height = models.FloatField(default=0, verbose_name="Высота (см)")

    # Данные синхронизации
    sync_data = models.JSONField(default=dict, blank=True, verbose_name="Данные синхронизации")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Заказ доставки"
        verbose_name_plural = "Заказы доставки"
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_id} - {self.tracking_number or 'Не создан'}"


# ========== Мессенджеры ==========

class MessengerIntegration(models.Model):
    """Модель интеграции с мессенджером"""
    integration = models.OneToOneField(IntegrationService, on_delete=models.CASCADE,
                                       limit_choices_to={'service_type': 'messenger'},
                                       related_name='messenger_settings', verbose_name="Интеграция")

    # Настройки бота
    bot_token = models.CharField(max_length=500, blank=True, verbose_name="Токен бота")
    bot_name = models.CharField(max_length=100, blank=True, verbose_name="Имя бота")
    webhook_secret = models.CharField(max_length=200, blank=True, verbose_name="Секрет webhook")

    # Настройки уведомлений
    notify_on_order = models.BooleanField(default=True, verbose_name="Уведомлять о заказах")
    notify_on_payment = models.BooleanField(default=True, verbose_name="Уведомлять об оплате")
    notify_on_delivery = models.BooleanField(default=True, verbose_name="Уведомлять о доставке")

    # Автоответы
    auto_reply = models.TextField(blank=True, verbose_name="Автоответчик")
    welcome_message = models.TextField(blank=True, verbose_name="Приветственное сообщение")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Настройки мессенджера"
        verbose_name_plural = "Настройки мессенджеров"

    def __str__(self):
        return f"{self.integration.name}"


class MessengerMessage(models.Model):
    """Модель сообщения в мессенджере"""
    DIRECTION_CHOICES = [
        ('inbound', 'Входящее'),
        ('outbound', 'Исходящее'),
    ]

    messenger = models.ForeignKey(IntegrationService, on_delete=models.CASCADE,
                                  limit_choices_to={'service_type': 'messenger'},
                                  related_name='messages',
                                  verbose_name="Мессенджер")

    user_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID пользователя")

    # Данные сообщения
    external_id = models.CharField(max_length=200, verbose_name="ID сообщения")
    chat_id = models.CharField(max_length=100, verbose_name="ID чата")
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, verbose_name="Направление")

    text = models.TextField(verbose_name="Текст сообщения")
    attachments = models.JSONField(default=list, blank=True, verbose_name="Вложения")

    # Статусы
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    is_processed = models.BooleanField(default=False, verbose_name="Обработано")

    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Время отправки")

    class Meta:
        verbose_name = "Сообщение мессенджера"
        verbose_name_plural = "Сообщения мессенджеров"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_direction_display()}: {self.text[:50]}"


# ========== Дополнительные сервисы ==========

class AdditionalService(models.Model):
    """Модель дополнительного сервиса"""
    SERVICE_CATEGORIES = [
        ('dadata', 'DaData'),
        ('maps', 'Карты'),
        ('crm', 'CRM'),
        ('analytics', 'Аналитика'),
        ('other', 'Другое'),
    ]

    integration = models.OneToOneField(IntegrationService, on_delete=models.CASCADE,
                                       limit_choices_to={'service_type': 'additional'},
                                       related_name='additional_settings', verbose_name="Интеграция")

    service_category = models.CharField(max_length=20, choices=SERVICE_CATEGORIES, verbose_name="Категория")

    # Общие настройки
    api_version = models.CharField(max_length=20, blank=True, verbose_name="Версия API")
    rate_limit = models.IntegerField(default=0, verbose_name="Лимит запросов в минуту")

    # Кэширование
    cache_enabled = models.BooleanField(default=True, verbose_name="Кэширование")
    cache_ttl = models.IntegerField(default=3600, verbose_name="Время жизни кэша (сек)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Дополнительный сервис"
        verbose_name_plural = "Дополнительные сервисы"

    def __str__(self):
        return f"{self.get_service_category_display()}: {self.integration.name}"





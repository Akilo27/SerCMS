from django.db import models
from django.conf import settings
import os
import uuid
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
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

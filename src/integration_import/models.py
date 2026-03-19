from django.conf import settings
from django.db import models
from django.core.validators import FileExtensionValidator


# Create your models here.
def get_upload_to(instance, filename):
    return f"import_elements/{instance.import_csv.id}/{filename}"


def get_xlsx_upload_to(instance, filename):
    return f"import_xlsx/{filename}"


class ImportCsv(models.Model):
    """Импорт"""

    TYPE = [
        (1, "Товары"),
        (2, "Категории товаров"),
        (3, "Вариации"),
        (4, "Производители"),
        (5, "Статьи"),
        (6, "Категории статей"),
        (7, "SEO"),
        (8, "Настройки"),
        (9, "Баннер"),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        blank=True,
        null=True,
    )
    type = models.PositiveIntegerField("Тип", choices=TYPE, blank=False, default=1)
    create = models.DateTimeField(auto_now=True, blank=True, null=True)
    status = models.BooleanField("Статус", default=False)
    created_all_elements = models.BooleanField("Созданы все элементы", default=False)
    quantity = models.PositiveIntegerField("Количество", blank=False, default=0)
    passed = models.PositiveIntegerField("Удачных", blank=False, default=0)
    added_element = models.PositiveIntegerField("Добавлено", blank=False, default=0)
    upload_element = models.PositiveIntegerField("Обновлено", blank=False, default=0)
    file = models.FileField(
        "файл",
        upload_to=get_xlsx_upload_to,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=["csv", "xlsx"])],
    )
    uploadfromdisk = models.ForeignKey(
        "UploadFromDiskImportCsv",
        on_delete=models.CASCADE,
        verbose_name="Загрузка",
        blank=True,
        null=True,
    )
    pause_status = models.BooleanField("Статус Паузы", default=False)
    last_element = models.ForeignKey(
        "ImportCsvElement",
        on_delete=models.CASCADE,
        verbose_name="Последний Элемент до Паузы",
        blank=True,
        null=True,
    )
    last_object = models.PositiveIntegerField(
        "Последний обьект до паузы", blank=True, null=True
    )

    def save(self, *args, **kwargs):
        # Сохраняем объект, чтобы получить первичный ключ
        super(ImportCsv, self).save(*args, **kwargs)

        # Подсчёт элементов со статусом True
        all_elements_have_status = (
            self.elements.filter(status=True).count() == self.elements.count()
        )
        if all_elements_have_status:
            self.status = True
            self.elements.all().delete()

        # Снова сохраняем объект, так как статус может измениться
        super(ImportCsv, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Импорт"
        verbose_name_plural = "Импорты"


class ImportCsvElement(models.Model):
    import_csv = models.ForeignKey(
        ImportCsv, on_delete=models.CASCADE, related_name="elements"
    )
    file = models.FileField(upload_to=get_upload_to)
    status = models.BooleanField(default=False)
    quantity = models.PositiveIntegerField("Количество", blank=False, default=0)
    passed = models.PositiveIntegerField("Удачных", blank=False, default=0)
    added_element = models.PositiveIntegerField("Добавленных", blank=False, default=0)
    upload_element = models.PositiveIntegerField("Обновленных", blank=False, default=0)

    def save(self, *args, **kwargs):
        if self.added_element != 0 or self.upload_element != 0:
            if self.added_element + self.upload_element == self.passed:
                if self.passed == self.quantity:
                    self.status = True
        super(ImportCsvElement, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Импорт Эл"
        verbose_name_plural = "Импорты Эл"


class YandexDiskIntegration(models.Model):
    key = models.TextField(verbose_name="Ключ", blank=True, null=True)
    activate = models.BooleanField("Активирован", default=False)

    class Meta:
        verbose_name = "Интеграция с Я.Диском"
        verbose_name_plural = "Интеграция с Я.Диском"


class UploadFromDiskImportCsv(models.Model):
    """Импорт"""

    TYPE = [
        (1, "Товары"),
        (2, "Категории товаров"),
        (3, "Вариации"),
        (4, "Производители"),
        (5, "Статьи"),
        (6, "Категории статей"),
        (7, "SEO"),
        (8, "Настройки"),
        (9, "Баннер"),
    ]
    type = models.PositiveIntegerField("Тип", choices=TYPE, blank=False, default=1)
    link = models.TextField(verbose_name="Ссылка на диск", blank=True, null=True)
    imagelink = models.TextField(
        verbose_name="Ссылка на папку с картинками", blank=True, null=True
    )
    activate = models.BooleanField("Активирован", default=False)
    last_attempt = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Импорт С Я.Диска"
        verbose_name_plural = "Импорт С Я.Диска"

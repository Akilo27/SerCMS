from django.db import models
import os
from django.contrib.sites.models import Site


# Create your models here.
class Documentations(models.Model):
    TYPE_CHOICES = [
        (0, "Сотрудник"),
        (1, "Обычный"),
        (2, "Юр лицо"),
        (3, "Компания"),
    ]
    type = models.SmallIntegerField(verbose_name="Тип", choices=TYPE_CHOICES, default=1)
    name = models.CharField(
        blank=True, verbose_name="Название", max_length=500, null=True
    )
    description = models.TextField("Описание")
    site = models.ManyToManyField(Site, verbose_name="Сайты", blank=True, default="1")

    class Meta:
        verbose_name = "Документация"
        verbose_name_plural = "Документации"

    def __str__(self):
        return self.name


class DocumentationsMedia(models.Model):
    documentations = models.ForeignKey(
        "Documentations", on_delete=models.CASCADE, related_name="documentations"
    )
    file = models.FileField(upload_to="documentations/%Y/%m/%d/")

    def get_file_name(self):
        return os.path.basename(self.file.name)

    class Meta:
        verbose_name = "Файл документации"
        verbose_name_plural = "Файлы документации"

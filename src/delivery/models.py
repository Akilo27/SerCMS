from django.db import models
from django.contrib.sites.models import Site
from webmain.models import SettingsGlobale


# TODO
# class Types(models.IntegerChoices):
#     pass


# Create your models here.
class DeliveryType(models.Model):
    """Страницы"""

    TYPE = [
        (1, "Яндекс Еда"),
        (2, "Почта россии"),
        (3, "СДЭК"),
        (4, "DHL"),
        (5, "ПЭК"),
        (6, "ДеловыеЛинии"),
        (7, "boxberry"),
    ]
    type = models.PositiveSmallIntegerField("Тип", choices=TYPE, blank=False, default=1)
    key_1 = models.CharField("Первый ключ (public_ley)", max_length=550)
    key_2 = models.CharField("Второй ключ (secret key)", max_length=550)
    content = models.TextField(blank=True, null=True, verbose_name="Описание")
    turn_on = models.BooleanField("Включить", default=False)
    setting = models.ForeignKey(
        SettingsGlobale,
        verbose_name="Настройки",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    site = models.ManyToManyField(Site, verbose_name="Сайты")

    class Meta:
        verbose_name = "Способ доставки"
        verbose_name_plural = "Способы доставок"

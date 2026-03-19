from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from useraccount.models import Profile
from .models import (
    Blogs,
    CategorysBlogs,
    SettingsGlobale,
    Seo,
    TagsBlogs,
    ContactPageInformation,
)
from PIL import Image
import os
from django.core.files.base import ContentFile
from io import BytesIO


"""|| Начало моделей из приложения Profile ||"""


@receiver(post_save, sender=Profile)
def convert_blog_images_to_webp(sender, instance, **kwargs):
    if instance.avatar:
        convert_image_to_webp(instance, "avatar")


"""|| Закончились моделей из приложения webmain ||"""


"""|| Начало моделей из приложения webmain ||"""


@receiver(post_save, sender=Blogs)
def convert_blog_images_to_webp(sender, instance, **kwargs):
    if instance.cover:
        convert_image_to_webp(instance, "cover")

    if instance.previev:
        convert_image_to_webp(instance, "previev")


@receiver(post_save, sender=CategorysBlogs)
def convert_category_images_to_webp(sender, instance, **kwargs):
    if instance.cover:
        convert_image_to_webp(instance, "cover")

    if instance.previev:
        convert_image_to_webp(instance, "previev")

    if instance.image:
        convert_image_to_webp(instance, "image")

    if instance.icon:
        convert_image_to_webp(instance, "icon")


@receiver(post_save, sender=TagsBlogs)
def convert_tags_images_to_webp(sender, instance, **kwargs):
    if instance.cover:
        convert_image_to_webp(instance, "cover")

    if instance.previev:
        convert_image_to_webp(instance, "previev")

    if instance.image:
        convert_image_to_webp(instance, "image")

    if instance.icon:
        convert_image_to_webp(instance, "icon")


@receiver(post_save, sender=Seo)
def convert_seo_image_to_webp(sender, instance, **kwargs):
    if instance.previev:
        convert_image_to_webp(instance, "previev")


@receiver(post_save, sender=ContactPageInformation)
def convert_seo_image_to_webp(sender, instance, **kwargs):
    if instance.image:
        convert_image_to_webp(instance, "image")


@receiver(post_save, sender=SettingsGlobale)
def convert_settingsglobale_image_to_webp(sender, instance, **kwargs):
    if instance.logo:
        convert_image_to_webp(instance, "logo")

    if instance.favicon:
        convert_image_to_webp(instance, "favicon")

    if instance.paymentmetod:
        convert_image_to_webp(instance, "paymentmetod")


"""|| Закончились модели из приложения webmain ||"""


"""Запускается функция генерации"""


def convert_image_to_webp(instance, field_name):
    image_field = getattr(instance, field_name)
    if isinstance(image_field, str):
        image_path = os.path.join(settings.MEDIA_ROOT, image_field)
    else:
        image_path = os.path.join(settings.MEDIA_ROOT, image_field.name)

    if os.path.exists(image_path):
        try:
            with Image.open(image_path) as img:
                if not image_path.endswith(".webp"):
                    # Прочитаем данные изображения напрямую из поля
                    image_field.open()
                    image_data = image_field.read()
                    image_field.close()

                    # Открываем изображение из байтового потока
                    image = Image.open(BytesIO(image_data))

                    # Сохраняем изображение в формате WEBP в буфер
                    buffer = BytesIO()
                    image.save(buffer, format="WEBP")
                    buffer.seek(0)

                    # Создаем новый файл с форматом WEBP
                    filename, ext = os.path.splitext(image_field.name)
                    webp_filename = f"{filename}.webp"
                    webp_content = ContentFile(buffer.getvalue(), name=webp_filename)

                    # Сохраняем новое изображение в поле
                    image_field.save(webp_filename, webp_content, save=False)

                    # Устанавливаем новый путь к изображению
                    setattr(instance, field_name, image_field.name)
                    instance.save()  # Сохраняем экземпляр с обновленным полем

        except Exception as e:
            print(f"Error converting image: {e}")
    else:
        print("Image file not found.")

import requests
import xml.etree.ElementTree as ET
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.files.base import ContentFile
from googletrans import Translator
from django.conf import settings
from django.utils.text import slugify
from django.db import transaction

from shop.models import (
    ImportHistory, Manufacturers, Products, ProductsVariable,
    ProductsGallery, Valute, Categories, Atribute, Variable
)

# Инициализация переводчика
translator = Translator()
SITE_LANGUAGES = [lang_code for lang_code, _ in settings.LANGUAGES]


@receiver(post_save, sender=ImportHistory)
def handle_import_file(sender, instance, **kwargs):
    """Обработчик импорта файла"""
    if instance.status != 'pending':
        print(f"ImportHistory {instance.id} статус не pending: {instance.status}")
        return

    print(f"Запуск импорта ImportHistory {instance.id}...")

    instance.status = 'in_progress'
    instance.started_at = timezone.now()
    instance.save()

    try:
        # Чтение данных из файла или URL
        if instance.file:
            xml_data = instance.file.read()
            print("Получены данные из файла")
        elif instance.file_url:
            response = requests.get(instance.file_url)
            response.raise_for_status()
            xml_data = response.content
            print("Получены данные из URL")
        else:
            raise ValueError("Не указан файл или ссылка для импорта")

        # Обработка XML данных
        process_product_xml(xml_data, instance)

        # Завершаем импорт
        instance.status = 'completed'
        print(f"Импорт ImportHistory {instance.id} завершен успешно.")
    except Exception as e:
        # Обработка ошибок
        instance.status = 'failed'
        print(f"Ошибка импорта ImportHistory {instance.id}: {e}")
    finally:
        instance.finished_at = timezone.now()
        instance.save()


# Функция перевода текста
def translate_text(text, src_lang, target_lang):
    try:
        translated = translator.translate(text, src=src_lang, dest=target_lang)
        return translated.text
    except Exception as e:
        print(f"Ошибка перевода '{text}' с {src_lang} на {target_lang}: {e}")
        return text  # Возвращаем оригинальный текст в случае ошибки


def get_or_create_variable_by_name(name):
    """Поиск или создание переменной по имени"""
    try:
        obj = Variable.objects.get(name=name)
        created = False
    except Variable.DoesNotExist:
        obj = Variable.objects.create(name=name)
        created = True

    print(f"Variable '{name}' {'created' if created else 'found'} with id {obj.id}")
    return obj


def get_option_value(secenek_element, tanim):
    """Извлечение значения из элемента выбора"""
    ozellikler = secenek_element.find('EkSecenekOzellik')
    if ozellikler is not None:
        for ozellik in ozellikler.findall('Ozellik'):
            if ozellik.get('Tanim') == tanim:
                return ozellik.get('Deger')
    return None


def download_image(url):
    """Загрузка изображения по URL"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        print(f"Изображение загружено: {url}")
        return ContentFile(response.content)
    except Exception as e:
        print(f"Не удалось скачать изображение {url}: {e}")
        return None


# Функция для получения или создания вариации продукта
def get_or_create_product_variation(name, product, quantity, price, cost_price, valute):
    try:
        variation, created = ProductsVariable.objects.update_or_create(
            product=product,
            name=name,
            defaults={
                'quantity': quantity,
                'price': price,
                'cost_price': cost_price,
                'valute': valute,
            }
        )
        if created:
            print(f"Создана новая вариация для продукта ID={product.id}")
        else:
            print(f"Обновлена существующая вариация для продукта ID={product.id}")
        return variation
    except Exception as e:
        print(f"Ошибка при создании или обновлении вариации для продукта ID={product.id}: {e}")
        return None


# Основная функция обработки XML данных
def process_product_xml(xml_data, import_instance):
    """Обработка XML файла с продуктами"""
    print("Начинаю обработку XML...")
    root = ET.fromstring(xml_data)

    manufacturer = Manufacturers.objects.get(shop_id=import_instance.shop_id)
    print(f"Производитель найден: {manufacturer.name}")

    valute = import_instance.valute or Valute.objects.filter(default=True).first()
    if not valute:
        raise ValueError("Валюта не найдена в ImportHistory и не задана по умолчанию.")

    print(f"Используем валюта: {valute.key} (ID: {valute.id})")

    default_src_lang = import_instance.language or 'en'

    for index, urun in enumerate(root.findall('.//Urun')):
        print(f"\n➡ Обработка товара #{index + 1}")
        try:
            with transaction.atomic():
                original_name = urun.findtext('UrunAdi', '').strip()
                original_description = urun.findtext('Aciklama', '').strip()

                # Определяем язык оригинала
                try:
                    detected_lang = translator.detect(original_name).lang
                except Exception:
                    detected_lang = default_src_lang
                print(f"Определён язык: {detected_lang}")

                # Переводим название и описание
                translations_name = {lang: translate_text(original_name, detected_lang, lang) for lang in
                                     SITE_LANGUAGES}
                translations_description = {lang: translate_text(original_description, detected_lang, lang) for lang in
                                            SITE_LANGUAGES}
                print(f"Переводы названия: {translations_name}")
                print(f"Переводы описания: {translations_description}")

                manufacturer_identifier = int(urun.findtext('UrunKartiID'))

                # Ищем или создаём продукт
                product, created = Products.objects.update_or_create(
                    manufacturer_identifier=manufacturer_identifier,
                    defaults={
                        'name': translations_name.get('ru', original_name),
                        'description': translations_description.get('ru', original_description),
                        'manufacturers': manufacturer,
                        'price': float(urun.findtext('SatisFiyati', '0.00')),
                        'costprice': float(urun.findtext('AlisFiyati', '0.00')),
                        'quantity': 0,
                        'type': 3,
                        'typeofchoice': 1,
                        'valute': valute,
                    }
                )

                if created:
                    print(f"Создан новый объект Products с ID={product.id}")
                else:
                    print(f"Обновлён существующий объект Products с ID={product.id}")

                # Сохраняем переводы
                for lang in SITE_LANGUAGES:
                    setattr(product, f'name_{lang}', translations_name[lang])
                    setattr(product, f'description_{lang}', translations_description[lang])
                product.save()

                # Привязываем продукт к сайту
                product.site.add(1)
                print(f"Продукт ID={product.id} привязан к сайту ID=1")

                # Обработка изображений
                resimler = urun.find('Resimler')
                if resimler:
                    resim_list = resimler.findall('Resim')
                    if resim_list:
                        main_img = download_image(resim_list[0].text.strip())
                        if main_img:
                            product.image.save(f"product_{product.id}.jpg", main_img)
                            print(f"Главное изображение сохранено для продукта ID={product.id}")
                    for i, resim in enumerate(resim_list):
                        gallery = ProductsGallery(products=product)
                        img = download_image(resim.text.strip())
                        if img:
                            gallery.image.save(f"gallery_{product.id}_{i}.jpg", img)
                            print(f"Добавлено изображение галереи #{i} для продукта ID={product.id}")
                        gallery.save()

                # Обработка категорий
                category_name = urun.findtext('Kategori', '').strip()
                category_translations = {lang: translate_text(category_name, detected_lang, lang) for lang in
                                         SITE_LANGUAGES}

                # Ищем категорию, переводим её
                categories = Categories.objects.filter(name=category_translations.get('ru', category_name))

                if categories.count() == 1:
                    category_obj = categories.first()
                    print(f"Категория '{category_obj.name}' найдена и добавлена к продукту ID={product.id}")
                elif categories.count() > 1:
                    print(f"Ошибка: Найдено несколько категорий с таким названием для продукта ID={product.id}")
                else:
                    # Создаём новую категорию, если не найдена
                    new_category = Categories.objects.create(name=category_translations.get('ru', category_name))
                    print(f"Создана новая категория '{new_category.name}' для продукта ID={product.id}")
                    category_obj = new_category

                # Добавление категории к продукту
                product.category.add(category_obj)
                product.save()

                # Обработка опций
                secenek_list = urun.findall('Secenek')
                for secenek in secenek_list:
                    option_name = secenek.find('SecenekAdi').text.strip()
                    option_value = get_option_value(secenek, 'Color')  # Пример для поиска цвета
                    variable = get_or_create_variable_by_name(option_name)
                    get_or_create_product_variation(option_value, product, 100, 19.99, 12.99, valute)

                print(f"Завершена обработка товара #{index + 1}")

        except Exception as e:
            print(f"Ошибка обработки товара #{index + 1}: {e}")

    print("Обработка XML завершена!")

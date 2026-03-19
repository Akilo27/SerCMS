# tasks.py
import time

from celery import shared_task
from django.db.utils import OperationalError
from django.db.models import Sum
from shop.models import (
    Products,
    Categories,
    Manufacturers,
    Site,
    ProductsGallery,
    Valute,
)
from integration_import.models import ImportCsv
import validators
import logging
import csv
import os
from django.core.exceptions import ObjectDoesNotExist
from .models import ImportCsv, ImportCsvElement
from webmain.models import (
    StockAvailability,
    Storage,
    SettingsGlobale,
    Categorys,
    Blogs,
    Seo,
    Banner,
)
from django.contrib.sites.models import Site
import requests
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO
import uuid
from django.core.files.uploadedfile import SimpleUploadedFile

logger = logging.getLogger(__name__)


def save_chunk(import_csv_instance, chunk, headers, import_type):
    chunk_data = "\n".join([";".join(headers)] + [";".join(row) for row in chunk])
    chunk_file = SimpleUploadedFile(
        f"{uuid.uuid4()}.csv", chunk_data.encode("utf-8"), content_type="text/csv"
    )
    chunk_file.seek(0)
    data_set = chunk_file.read().decode("UTF-8")
    csv_reader = csv.reader(data_set.splitlines(), delimiter=";")
    quantity_rows = sum(1 for row in csv_reader) - 1
    import_csv_element = ImportCsvElement.objects.create(
        import_csv=import_csv_instance, file=chunk_file, quantity=quantity_rows
    )
    import_csv_instance.elements.add(import_csv_element)
    return import_csv_element


def download_image(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Ошибка при загрузке изображения: {e}")
        return None

    content_type = response.headers.get("Content-Type", "")
    if "image" not in content_type:
        print("Загруженный файл не является изображением.")
        return None

    try:
        image = Image.open(BytesIO(response.content))
        webp_image = BytesIO()
        image.save(webp_image, format="WebP")
        webp_image.seek(0)

    except Exception as e:
        print(f"Ошибка при преобразовании изображения в WebP: {e}")
        return None

    original_filename = os.path.basename(image_url.split("?")[0])

    original_name_without_ext, _ = os.path.splitext(original_filename)
    webp_filename = f"{original_name_without_ext}.webp"

    return ContentFile(webp_image.read(), name=webp_filename)


def to_boolean(value):
    if value == "1":
        return True
    elif value == "0":
        return False
    return False


@shared_task
def start_of_processing_csv(import_csv_id):
    instance = ImportCsv.objects.get(id=import_csv_id)
    if instance.status:
        return  # Задача уже завершена или все элементы созданы

    csv_file = instance.file
    csv_file.seek(0)
    data_set = csv_file.read().decode("UTF-8")
    csv_reader = csv.reader(data_set.splitlines(), delimiter=";")

    headers = next(csv_reader)  # Сохраняем заголовки
    chunk_size = 1000  # Размер части
    chunk = []

    row_limit = instance.quantity
    processed_rows = 0

    import_csv_elements = []

    for row in csv_reader:
        if instance.created_all_elements:
            break
        chunk.append(row)
        processed_rows += 1

        if len(chunk) >= chunk_size or processed_rows >= row_limit:
            import_csv_element = save_chunk(instance, chunk, headers, instance.type)
            import_csv_elements.append(import_csv_element)
            chunk = []

        if processed_rows >= row_limit:
            break

    # Сохраняем оставшиеся данные
    if chunk:
        import_csv_element = save_chunk(instance, chunk, headers, instance.type)
        import_csv_elements.append(import_csv_element)

    # Устанавливаем флаг после создания всех ImportCsvElement
    instance.created_all_elements = True
    instance.save()

    # Запуск задач обработки для всех созданных элементов
    for element in import_csv_elements:
        if instance.type == 1:
            process_product_csv_task.delay(element.id, element.file.path)
        elif instance.type == 2:
            process_category_csv_task.delay(element.id, element.file.path)
        elif instance.type == 6:
            process_categories_csv_task.delay(element.id, element.file.path)
        elif instance.type == 4:
            process_manufacturer_csv_task.delay(element.id, element.file.path)
        elif instance.type == 5:
            process_blog_csv_task.delay(element.id, element.file.path)
        elif instance.type == 7:
            process_seo_csv_task.delay(element.id, element.file.path)
        elif instance.type == 9:
            process_banner_csv_task.delay(element.id, element.file.path)
        else:
            logger.error("Неизвестный тип импорта.", exc_info=True)


@shared_task
def process_product_csv_task(import_csv_id, csv_file_content):
    import_csv_instance = ImportCsvElement.objects.get(id=import_csv_id, status=False)
    import_csv = import_csv_instance.import_csv
    try:
        with open(csv_file_content, "r", encoding="UTF-8") as file:
            data_set = file.read()
        csv_reader = csv.reader(data_set.splitlines(), delimiter=";")
        header = next(csv_reader)
        required_headers = [
            "id",
            "name",
            "price",
            "category",
            "manufacturers",
            "image",
            "order",
            "review",
            "faqs",
            "site",
            "valute",
        ]
        optional_headers = [
            "fragment",
            "description",
            "slug",
            "title",
            "content",
            "discount",
            "quantity",
            "review_rating",
            "type",
            "comment",
            "images",
            "atribute",
            "stock",
        ]

        for row in csv_reader:
            try:
                product_data = {
                    field: row[header.index(field)].strip() if field in header else None
                    for field in required_headers + optional_headers
                }

                if product_data["slug"] and "%" in product_data["slug"]:
                    product_data["slug"] = ""

                product_data["price"] = float(product_data["price"])
                product_data["order"] = to_boolean(product_data["order"])
                product_data["review"] = to_boolean(product_data["review"])
                product_data["faqs"] = to_boolean(product_data["faqs"])
                product_data["comment"] = to_boolean(product_data.get("comment", "0"))

                try:
                    product_data["image_content"] = download_image(
                        product_data["image"]
                    )
                except Exception:
                    product_data["image_content"] = None

                sites = []
                for site_id in product_data["site"].split("."):
                    try:
                        site = Site.objects.get(id=site_id.strip())
                        sites.append(site)
                    except ObjectDoesNotExist:
                        continue

                categories = []
                parent_category = None
                for category_name in product_data["category"].split("|"):
                    category_name = category_name.strip()
                    parent_category, created = Categories.objects.get_or_create(
                        name=category_name, defaults={"parent": parent_category}
                    )
                    if created:
                        parent_category.site.set(sites)
                    categories.append(parent_category)

                manufacturer, created = Manufacturers.objects.get_or_create(
                    name=product_data["manufacturers"]
                )
                if created:
                    manufacturer.site.set(sites)
                valute, created = Valute.objects.get_or_create(
                    key=product_data["valute"]
                )

                manufacturer_identifier = product_data["id"]

                # Проверка на наличие значения в manufacturer_identifier
                if not manufacturer_identifier:
                    logger.error(
                        f'Отсутствует идентификатор производителя для продукта с именем: {product_data["name"]} с id {product_data["id"]} полный дата {product_data}'
                    )
                    continue

                product, product_created = Products.objects.update_or_create(
                    manufacturer_identifier=manufacturer_identifier,
                    manufacturers=manufacturer,
                    defaults={
                        "name": product_data["name"],
                        "fragment": product_data["fragment"],
                        "description": product_data["description"],
                        "slug": product_data["slug"],
                        "title": product_data["title"],
                        "content": product_data["content"],
                        "image": product_data["image_content"],
                        "price": product_data["price"],
                        "discount": product_data["discount"],
                        "quantity": product_data["quantity"],
                        "review_rating": product_data["review_rating"],
                        "order": product_data["order"],
                        "review": product_data["review"],
                        "faqs": product_data["faqs"],
                        "comment": product_data["comment"],
                        "valute": valute,
                    },
                )
                if product_created:
                    import_csv_instance.added_element += 1
                    import_csv_instance.save()
                else:
                    import_csv_instance.upload_element += 1
                    import_csv_instance.save()
                product.category.set(categories)
                product.site.set(sites)

                if product_data["images"]:
                    for image_url in product_data["images"].split(","):
                        try:
                            image_content = download_image(image_url.strip())
                            if image_content:
                                gallery = ProductsGallery(products=product)
                                gallery.image.save(
                                    image_content.name, image_content, save=True
                                )
                        except Exception:
                            continue

                if product_data["atribute"]:
                    for pair in product_data["atribute"].split("|"):
                        if not pair.strip():
                            continue
                        try:
                            storage_id, quantity = map(int, pair.split(":"))
                            storage = Storage.objects.get(id=storage_id)
                            stock_availability = StockAvailability(
                                products=product, storage=storage, quantity=quantity
                            )
                            stock_availability.save()
                        except (ValueError, ObjectDoesNotExist):
                            continue

                if product_data["stock"]:
                    for pair in product_data["stock"].split(","):
                        if not pair.strip():
                            continue
                        try:
                            storage_id, quantity = map(int, pair.split(":"))
                            storage = Storage.objects.get(id=storage_id)
                            stock_availability = StockAvailability(
                                products=product, storage=storage, quantity=quantity
                            )
                            stock_availability.save()
                        except (ValueError, ObjectDoesNotExist):
                            continue

                import_csv_instance.passed += 1
                import_csv_instance.save()

                import_csv.passed = import_csv.elements.aggregate(Sum("passed"))[
                    "passed__sum"
                ]
                import_csv.added_element = import_csv.elements.aggregate(
                    Sum("added_element")
                )["added_element__sum"]
                import_csv.upload_element = import_csv.elements.aggregate(
                    Sum("upload_element")
                )["upload_element__sum"]
                import_csv.save()
            except OperationalError as e:
                logger.error(f"Database is locked: {e}. Retrying...", exc_info=True)
                time.sleep(1)
            except (IndexError, ValueError) as e:
                logger.error(f"Ошибка при обработке строки: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Произошла ошибка: {e}", exc_info=True)
        import_csv_instance.status = True
        import_csv_instance.save()
        import_csv.save()

    except Exception:
        import_csv_instance.status = False
        import_csv_instance.save()


@shared_task
def process_category_csv_task(import_csv_id, csv_file_content):
    import_csv_element = ImportCsvElement.objects.get(id=import_csv_id)
    import_csv = import_csv_element.import_csv

    def process_csv():
        try:
            with open(csv_file_content, "r", encoding="UTF-8") as file:
                data_set = file.read()
            csv_reader = csv.reader(data_set.splitlines(), delimiter=";")

            try:
                header = next(csv_reader)
            except StopIteration:
                logger.error("Пустой CSV файл.")
                import_csv_element.status = False
                import_csv_element.save()
                return

            required_headers = [
                "id",
                "name",
                "description",
                "title",
                "content",
                "slug",
                "site",
                "cover",
                "icon",
                "image",
                "parent",
            ]
            missing_headers = [h for h in required_headers if h not in header]
            if missing_headers:
                logger.error(f"Отсутствуют необходимые заголовки: {missing_headers}")
                import_csv_element.status = False
                import_csv_element.save()
                return

            passed_count = 0
            categories = []

            for row in csv_reader:
                try:
                    category_data = {
                        field: row[header.index(field)].strip()
                        if field in header
                        else None
                        for field in required_headers
                    }

                    # Получение сайтов
                    site_ids = category_data["site"].split(",")
                    sites = []
                    for site_id in site_ids:
                        try:
                            site = Site.objects.get(id=site_id.strip())
                            sites.append(site)
                        except Site.DoesNotExist:
                            logger.warning(f"Сайт с ID {site_id} не найден. Пропущено.")

                    # Получение родительской категории
                    parent_category = None
                    parent_id = category_data.get("parent")
                    if parent_id:
                        try:
                            parent_category = Categories.objects.get(
                                id=parent_id.strip()
                            )
                        except Categories.DoesNotExist:
                            logger.warning(
                                f"Родительская категория с ID {parent_id} не найдена. Пропущено."
                            )

                    # Загрузка изображений
                    for field in ["cover", "icon", "image"]:
                        if field not in category_data or not category_data[field]:
                            continue
                        image_url = category_data[field]
                        if not validators.url(image_url):
                            logger.warning(
                                f"Неверный URL изображения ({field}): {image_url}"
                            )
                            continue
                        try:
                            image_content = download_image(image_url)
                            if image_content is None:
                                logger.warning(
                                    f"Не удалось загрузить изображение ({field}): {image_url}"
                                )
                                continue
                        except Exception as e:
                            logger.warning(
                                f"Ошибка при загрузке изображения ({field}): {e}"
                            )
                            continue
                        category_data[f"{field}_content"] = image_content

                    # Создание или обновление категории
                    category_defaults = {
                        "name": category_data["name"],
                        "description": category_data["description"],
                        "title": category_data["title"],
                        "content": category_data["content"],
                        "slug": category_data["slug"],
                        "parent": parent_category,
                    }
                    category, created = Categories.objects.update_or_create(
                        id=category_data["id"], defaults=category_defaults
                    )

                    if created:
                        import_csv_element.added_element += 1
                        import_csv_element.save()
                    else:
                        import_csv_element.upload_element += 1
                        import_csv_element.save()

                    # Сохраняем информацию о категории (category, created) в списке categories
                    categories.append((category, created))

                    # Сохранение изображений
                    for field in ["cover", "icon", "image"]:
                        if f"{field}_content" in category_data:
                            getattr(category, field).save(
                                f"{category_data['id']}_{field}.jpg",
                                category_data[f"{field}_content"],
                                save=True,
                            )

                    # Установка сайтов
                    category.site.set(sites)

                    import_csv_element.passed += 1
                    import_csv_element.save()

                    import_csv.passed = import_csv.elements.aggregate(Sum("passed"))[
                        "passed__sum"
                    ]
                    import_csv.added_element = import_csv.elements.aggregate(
                        Sum("added_element")
                    )["added_element__sum"]
                    import_csv.upload_element = import_csv.elements.aggregate(
                        Sum("upload_element")
                    )["upload_element__sum"]
                    import_csv.save()

                    if created:
                        logger.info(f"Создана новая категория: {category_data['id']}")
                    else:
                        logger.info(
                            f"Обновлена существующая категория: {category_data['id']}"
                        )
                except (IndexError, ValueError) as e:
                    logger.error(f"Ошибка при обработке строки: {e}")
                except Exception as e:
                    logger.error(f"Произошла ошибка: {e}", exc_info=True)

            import_csv_element.status = True
            import_csv_element.save()
            all_elements_have_status = (
                import_csv.elements.all().aggregate(all_status_true=Sum("status"))[
                    "all_status_true"
                ]
                == import_csv.elements.count()
            )
            if all_elements_have_status:
                import_csv.status = True
                import_csv.elements.all().delete()
                import_csv.save()
        except Exception as e:
            import_csv_element.status = False
            import_csv_element.save()
            logger.error(f"Произошла ошибка при обработке CSV: {e}", exc_info=True)

    process_csv()


@shared_task
def process_categories_csv_task(import_csv_id, csv_file_content):
    import_csv_element = ImportCsvElement.objects.get(id=import_csv_id)
    import_csv = import_csv_element.import_csv

    def process_csv():
        try:
            with open(csv_file_content, "r", encoding="UTF-8") as file:
                data_set = file.read()
            csv_reader = csv.reader(data_set.splitlines(), delimiter=";")

            try:
                header = next(csv_reader)
            except StopIteration:
                logger.error("Пустой CSV файл.")
                import_csv_element.status = False
                import_csv_element.save()
                return

            required_headers = [
                "id",
                "name",
                "description",
                "title",
                "content",
                "slug",
                "site",
                "cover",
                "icon",
                "image",
                "parent",
            ]
            missing_headers = [h for h in required_headers if h not in header]
            if missing_headers:
                logger.error(f"Отсутствуют необходимые заголовки: {missing_headers}")
                import_csv_element.status = False
                import_csv_element.save()
                return

            passed_count = 0
            categories = []

            for row in csv_reader:
                try:
                    category_data = {
                        field: row[header.index(field)].strip()
                        if field in header
                        else None
                        for field in required_headers
                    }

                    # Получение сайтов
                    site_ids = category_data["site"].split(",")
                    sites = []
                    for site_id in site_ids:
                        try:
                            site = Site.objects.get(id=site_id.strip())
                            sites.append(site)
                        except Site.DoesNotExist:
                            logger.warning(f"Сайт с ID {site_id} не найден. Пропущено.")

                    # Получение родительской категории
                    parent_category = None
                    parent_id = category_data.get("parent")
                    if parent_id:
                        try:
                            parent_category = Categories.objects.get(
                                id=parent_id.strip()
                            )
                        except Categories.DoesNotExist:
                            logger.warning(
                                f"Родительская категория с ID {parent_id} не найдена. Пропущено."
                            )

                    # Загрузка изображений
                    for field in ["cover", "icon", "image"]:
                        if field not in category_data or not category_data[field]:
                            continue
                        image_url = category_data[field]
                        if not validators.url(image_url):
                            logger.warning(
                                f"Неверный URL изображения ({field}): {image_url}"
                            )
                            continue  # Skip processing this row
                        try:
                            image_content = download_image(image_url)
                            if image_content is None:
                                logger.warning(
                                    f"Не удалось загрузить изображение ({field}): {image_url}"
                                )
                                continue
                        except Exception as e:
                            logger.warning(
                                f"Ошибка при загрузке изображения ({field}): {e}"
                            )
                            continue
                        category_data[f"{field}_content"] = image_content

                    # Создание или обновление категории
                    category_defaults = {
                        "name": category_data["name"],
                        "description": category_data["description"],
                        "title": category_data["title"],
                        "content": category_data["content"],
                        "slug": category_data["slug"],
                        "parent": parent_category,
                    }
                    category, created = Categories.objects.update_or_create(
                        id=category_data["id"], defaults=category_defaults
                    )

                    if created:
                        import_csv_element.added_element += 1
                        import_csv_element.save()
                    else:
                        import_csv_element.upload_element += 1
                        import_csv_element.save()

                    # Сохраняем информацию о категории (category, created) в списке categories
                    categories.append((category, created))

                    # Сохранение изображений
                    for field in ["cover", "icon", "image"]:
                        if f"{field}_content" in category_data:
                            getattr(category, field).save(
                                f"{category_data['id']}_{field}.jpg",
                                category_data[f"{field}_content"],
                                save=True,
                            )

                    # Установка сайтов
                    category.site.set(sites)

                    import_csv_element.passed += 1
                    import_csv_element.save()

                    import_csv.passed = import_csv.elements.aggregate(Sum("passed"))[
                        "passed__sum"
                    ]
                    import_csv.added_element = import_csv.elements.aggregate(
                        Sum("added_element")
                    )["added_element__sum"]
                    import_csv.upload_element = import_csv.elements.aggregate(
                        Sum("upload_element")
                    )["upload_element__sum"]
                    import_csv.save()
                    if created:
                        logger.info(f"Создана новая категория: {category_data['id']}")
                    else:
                        logger.info(
                            f"Обновлена существующая категория: {category_data['id']}"
                        )
                except (IndexError, ValueError) as e:
                    logger.error(f"Ошибка при обработке строки: {e}")
                except Exception as e:
                    logger.error(f"Произошла ошибка: {e}", exc_info=True)

            # Обновить поле added_element и upload_element в экземпляре import_csv после обработки

            import_csv_element.status = True
            import_csv_element.save()

            all_elements_have_status = (
                import_csv.elements.all().aggregate(all_status_true=Sum("status"))[
                    "all_status_true"
                ]
                == import_csv.elements.count()
            )
            if all_elements_have_status:
                import_csv.status = True
                import_csv.elements.all().delete()
                import_csv.save()

        except Exception as e:
            import_csv_element.status = False
            import_csv_element.save()
            logger.error(f"Произошла ошибка при обработке CSV: {e}", exc_info=True)

    process_csv()


@shared_task
def process_manufacturer_csv_task(import_csv_id, csv_file_content):
    import_csv_element = ImportCsvElement.objects.get(id=import_csv_id)
    import_csv = import_csv_element.import_csv

    def process_csv():
        try:
            with open(csv_file_content, "r", encoding="UTF-8") as file:
                data_set = file.read()
            csv_reader = csv.reader(data_set.splitlines(), delimiter=";")

            try:
                header = next(csv_reader)
            except StopIteration:
                logger.error("Пустой CSV файл.")
                import_csv_element.status = False
                import_csv_element.save()
                return

            required_headers = [
                "id",
                "name",
                "description",
                "title",
                "content",
                "slug",
                "site",
                "cover",
                "image",
            ]
            missing_headers = [h for h in required_headers if h not in header]
            if missing_headers:
                logger.error(f"Отсутствуют необходимые заголовки: {missing_headers}")
                import_csv_element.status = False
                import_csv_element.save()
                return

            passed_count = 0
            manufacturers = []

            for row in csv_reader:
                try:
                    manufacturer_data = {
                        field: row[header.index(field)].strip()
                        if field in header
                        else None
                        for field in required_headers
                    }

                    # Получение сайтов
                    site_ids = manufacturer_data["site"].split(",")
                    sites = []
                    for site_id in site_ids:
                        try:
                            site = Site.objects.get(id=site_id.strip())
                            sites.append(site)
                        except ObjectDoesNotExist:
                            logger.warning(f"Сайт с ID {site_id} не найден. Пропущено.")

                    # Загрузка изображений
                    for field in ["cover", "image"]:
                        if (
                            field not in manufacturer_data
                            or not manufacturer_data[field]
                        ):
                            continue
                        image_url = manufacturer_data[field]
                        if not validators.url(image_url):
                            logger.warning(
                                f"Неверный URL изображения ({field}): {image_url}"
                            )
                            continue
                        try:
                            image_content = download_image(image_url)
                            if image_content is None:
                                logger.warning(
                                    f"Не удалось загрузить изображение ({field}): {image_url}"
                                )
                                continue
                        except Exception as e:
                            logger.warning(
                                f"Ошибка при загрузке изображения ({field}): {e}"
                            )
                            continue
                        manufacturer_data[f"{field}_content"] = image_content

                    # Создание или обновление производителя
                    manufacturer_defaults = {
                        "name": manufacturer_data["name"],
                        "description": manufacturer_data["description"],
                        "title": manufacturer_data["title"],
                        "content": manufacturer_data["content"],
                        "slug": manufacturer_data["slug"]
                        if manufacturer_data["slug"]
                        else None,
                    }
                    manufacturer, created = Manufacturers.objects.update_or_create(
                        id=manufacturer_data["id"], defaults=manufacturer_defaults
                    )

                    if created:
                        import_csv_element.added_element += 1
                        import_csv_element.save()
                    else:
                        import_csv_element.upload_element += 1
                        import_csv_element.save()

                    # Сохранение информации о производителе (manufacturer, created) в списке manufacturers
                    manufacturers.append((manufacturer, created))

                    # Сохранение изображений
                    for field in ["cover", "image"]:
                        if f"{field}_content" in manufacturer_data:
                            getattr(manufacturer, field).save(
                                f"{manufacturer_data['id']}_{field}.jpg",
                                manufacturer_data[f"{field}_content"],
                                save=True,
                            )

                    # Установка сайтов
                    manufacturer.site.set(sites)

                    import_csv_element.passed += 1
                    import_csv_element.save()

                    import_csv.passed = import_csv.elements.aggregate(Sum("passed"))[
                        "passed__sum"
                    ]
                    import_csv.added_element = import_csv.elements.aggregate(
                        Sum("added_element")
                    )["added_element__sum"]
                    import_csv.upload_element = import_csv.elements.aggregate(
                        Sum("upload_element")
                    )["upload_element__sum"]
                    import_csv.save()
                    if created:
                        logger.info(
                            f"Создан новый производитель: {manufacturer_data['id']}"
                        )
                    else:
                        logger.info(
                            f"Обновлен существующий производитель: {manufacturer_data['id']}"
                        )
                except (IndexError, ValueError) as e:
                    logger.error(f"Ошибка при обработке строки: {e}")
                except Exception as e:
                    logger.error(f"Произошла ошибка: {e}", exc_info=True)

            # Обновление поля added_element и upload_element в экземпляре import_csv после обработки
            import_csv_element.status = True
            import_csv_element.save()

            all_elements_have_status = (
                import_csv.elements.all().aggregate(all_status_true=Sum("status"))[
                    "all_status_true"
                ]
                == import_csv.elements.count()
            )
            if all_elements_have_status:
                import_csv.status = True
                import_csv.elements.all().delete()
                import_csv.save()

        except Exception as e:
            import_csv_element.status = False
            import_csv_element.save()
            logger.error(f"Произошла ошибка при обработке CSV: {e}", exc_info=True)

    process_csv()


@shared_task
def process_blog_csv_task(import_csv_id, csv_file_content):
    import_csv_element = ImportCsvElement.objects.get(id=import_csv_id)
    import_csv = import_csv_element.import_csv

    def process_csv():
        try:
            with open(csv_file_content, "r", encoding="UTF-8") as file:
                data_set = file.read()
            csv_reader = csv.reader(data_set.splitlines(), delimiter=";")

            try:
                header = next(csv_reader)
            except StopIteration:
                logger.error("Пустой CSV файл.")
                import_csv_element.status = False
                import_csv_element.save()
                return

            required_headers = [
                "id",
                "site",
                "author",
                "resource",
                "category",
                "name",
                "description",
                "previev",
                "title",
                "content",
                "propertytitle",
                "propertydescription",
                "slug",
                "cover",
            ]
            missing_headers = [h for h in required_headers if h not in header]
            if missing_headers:
                logger.error(f"Отсутствуют необходимые заголовки: {missing_headers}")
                import_csv_element.status = False
                import_csv_element.save()
                return

            optional_headers = []

            passed_count = 0
            blogss = []

            for row in csv_reader:
                try:
                    blogs_data = {}
                    for field in required_headers + optional_headers:
                        if field in header:
                            blogs_data[field] = row[header.index(field)].strip()
                        else:
                            blogs_data[field] = None

                    if blogs_data["slug"] and "%" in blogs_data["slug"]:
                        logger.info("Значение 'slug' содержит '%', оставляем пустым.")
                        blogs_data["slug"] = ""

                    try:
                        blogs_data["image_content"] = download_image(
                            blogs_data["cover"]
                        )
                        if blogs_data["image_content"] is None:
                            logger.warning(
                                f"Не удалось загрузить изображение: {blogs_data['cover']}"
                            )
                    except Exception as e:
                        logger.warning(f"Ошибка при загрузке изображения: {e}")
                        blogs_data["image_content"] = None

                    try:
                        blogs_data["previev_content"] = download_image(
                            blogs_data["previev"]
                        )
                        if blogs_data["previev_content"] is None:
                            logger.warning(
                                f"Не удалось загрузить изображение: {blogs_data['previev']}"
                            )
                    except Exception as e:
                        logger.warning(f"Ошибка при загрузке изображения: {e}")
                        blogs_data["previev_content"] = None

                    site_ids = blogs_data["site"].split(",")
                    sites = []
                    for site_id in site_ids:
                        try:
                            site = Site.objects.get(id=site_id.strip())
                            sites.append(site)
                        except ObjectDoesNotExist:
                            logger.warning(f"Сайт с ID {site_id} не найден. Пропущено.")

                    category_names = blogs_data["category"].split("|")
                    categories = []
                    parent_category = None
                    for category_name in category_names:
                        category_name = category_name.strip()
                        if not parent_category:
                            parent_category, created = Categorys.objects.get_or_create(
                                name=category_name
                            )
                            if created:
                                parent_category.site.set(sites)
                        else:
                            child_category, created = Categorys.objects.get_or_create(
                                name=category_name, defaults={"parent": parent_category}
                            )
                            if created:
                                child_category.site.set(sites)
                            parent_category = child_category
                        categories.append(parent_category)

                    blogs, created = Blogs.objects.get_or_create(
                        id=blogs_data["id"],
                        defaults={
                            "author_id": blogs_data["author"]
                            if blogs_data["author"]
                            else None,
                            "resource": blogs_data["resource"],
                            "name": blogs_data["name"],
                            "description": blogs_data["description"],
                            "title": blogs_data["title"],
                            "content": blogs_data["content"],
                            "cover": blogs_data["image_content"],
                            "previev": blogs_data["previev_content"],
                            "propertytitle": blogs_data["propertytitle"],
                            "propertydescription": blogs_data["propertydescription"],
                            "slug": blogs_data["slug"],
                        },
                    )
                    if created:
                        import_csv_element.added_element += 1
                        import_csv_element.save()
                    else:
                        import_csv_element.upload_element += 1
                        import_csv_element.save()
                    blogss.append((blogs, created))

                    if created:
                        logger.info(f"Создан новый продукт: {blogs_data['id']}")
                    else:
                        logger.info(
                            f"Обновлен существующий продукт: {blogs_data['id']}"
                        )
                        blogs.author = blogs_data["author"]
                        blogs.resource = blogs_data["resource"]
                        blogs.name = blogs_data["name"]
                        blogs.description = blogs_data["description"]
                        blogs.title = blogs_data["title"]
                        blogs.content = blogs_data["content"]
                        blogs.cover = blogs_data["image_content"]
                        blogs.previev = blogs_data["previev_content"]
                        blogs.propertytitle = blogs_data["propertytitle"]
                        blogs.propertydescription = blogs_data["propertydescription"]
                        blogs.slug = blogs_data["slug"]
                        blogs.save()

                    blogs.category.set(categories)
                    blogs.site.set(sites)

                    import_csv_element.passed += 1
                    import_csv_element.save()

                    import_csv.passed = import_csv.elements.aggregate(Sum("passed"))[
                        "passed__sum"
                    ]
                    import_csv.added_element = import_csv.elements.aggregate(
                        Sum("added_element")
                    )["added_element__sum"]
                    import_csv.upload_element = import_csv.elements.aggregate(
                        Sum("upload_element")
                    )["upload_element__sum"]
                    import_csv.save()

                except (IndexError, ValueError) as e:
                    logger.error(f"Ошибка при обработке строки: {e}")
                except Exception as e:
                    logger.error(f"Произошла ошибка: {e}", exc_info=True)

            import_csv_element.status = True
            import_csv_element.save()

            all_elements_have_status = (
                import_csv.elements.all().aggregate(all_status_true=Sum("status"))[
                    "all_status_true"
                ]
                == import_csv.elements.count()
            )
            if all_elements_have_status:
                import_csv.status = True
                import_csv.elements.all().delete()
                import_csv.save()

        except Exception as e:
            import_csv_element.status = False
            import_csv_element.save()
            logger.error(f"Произошла ошибка при обработке CSV: {e}", exc_info=True)

    process_csv()


@shared_task
def process_seo_csv_task(import_csv_id, csv_file_content):
    import_csv_element = ImportCsvElement.objects.get(id=import_csv_id)
    import_csv = import_csv_element.import_csv

    def process_csv():
        try:
            with open(csv_file_content, "r", encoding="UTF-8") as file:
                data_set = file.read()
            csv_reader = csv.reader(data_set.splitlines(), delimiter=";")

            try:
                header = next(csv_reader)
            except StopIteration:
                logger.error("Пустой CSV файл.")
                import_csv_element.status = False
                import_csv_element.save()
                return

            required_headers = [
                "id",
                "setting",
                "pagetype",
                "previev",
                "title",
                "description",
                "propertytitle",
                "propertydescription",
            ]
            missing_headers = [h for h in required_headers if h not in header]
            if missing_headers:
                logger.error(f"Отсутствуют необходимые заголовки: {missing_headers}")
                import_csv_element.status = False
                import_csv_element.save()
                return

            optional_headers = []

            passed_count = 0
            seos = []

            for row in csv_reader:
                try:
                    seo_data = {}
                    for field in required_headers + optional_headers:
                        if field in header:
                            seo_data[field] = row[header.index(field)].strip()
                        else:
                            seo_data[field] = None

                    try:
                        seo_data["previev_content"] = download_image(
                            seo_data["previev"]
                        )
                        if seo_data["previev_content"] is None:
                            logger.warning(
                                f"Не удалось загрузить изображение: {seo_data['previev']}"
                            )
                    except Exception as e:
                        logger.warning(f"Ошибка при загрузке изображения: {e}")
                        seo_data["previev_content"] = None

                    setting_id = int(seo_data["setting"])
                    settings_globale = SettingsGlobale.objects.get(id=setting_id)

                    seo, created = Seo.objects.get_or_create(
                        id=seo_data["id"],
                        defaults={
                            "setting": settings_globale,
                            "pagetype": seo_data["pagetype"],
                            "previev": seo_data["previev_content"],
                            "title": seo_data["title"],
                            "description": seo_data["description"],
                            "propertytitle": seo_data["propertytitle"],
                            "propertydescription": seo_data["propertydescription"],
                        },
                    )
                    if created:
                        import_csv_element.added_element += 1
                        import_csv_element.save()
                    else:
                        import_csv_element.upload_element += 1
                        import_csv_element.save()
                    seos.append((seo, created))

                    if created:
                        logger.info(f"Создан новый продукт: {seo_data['id']}")
                    else:
                        logger.info(f"Обновлен существующий продукт: {seo_data['id']}")
                        seo.pagetype = seo_data["pagetype"]
                        seo.setting = settings_globale
                        seo.previev = seo_data["previev_content"]
                        seo.title = seo_data["title"]
                        seo.description = seo_data["description"]
                        seo.propertytitle = seo_data["propertytitle"]
                        seo.propertydescription = seo_data["propertydescription"]
                        seo.save()

                    import_csv_element.passed += 1
                    import_csv_element.save()

                    import_csv.passed = import_csv.elements.aggregate(Sum("passed"))[
                        "passed__sum"
                    ]
                    import_csv.added_element = import_csv.elements.aggregate(
                        Sum("added_element")
                    )["added_element__sum"]
                    import_csv.upload_element = import_csv.elements.aggregate(
                        Sum("upload_element")
                    )["upload_element__sum"]
                    import_csv.save()

                except (IndexError, ValueError) as e:
                    logger.error(f"Ошибка при обработке строки: {e}")
                except Exception as e:
                    logger.error(f"Произошла ошибка: {e}", exc_info=True)
            import_csv_element.status = True
            import_csv_element.save()

            all_elements_have_status = (
                import_csv.elements.all().aggregate(all_status_true=Sum("status"))[
                    "all_status_true"
                ]
                == import_csv.elements.count()
            )
            if all_elements_have_status:
                import_csv.status = True
                import_csv.elements.all().delete()
                import_csv.save()

        except Exception as e:
            import_csv_element.status = False
            import_csv_element.save()
            logger.error(f"Произошла ошибка при обработке CSV: {e}", exc_info=True)

    process_csv()


@shared_task
def process_banner_csv_task(import_csv_id, csv_file_content):
    import_csv_element = ImportCsvElement.objects.get(id=import_csv_id)
    import_csv = import_csv_element.import_csv

    def process_csv():
        try:
            with open(csv_file_content, "r", encoding="UTF-8") as file:
                data_set = file.read()
            csv_reader = csv.reader(data_set.splitlines(), delimiter=";")

            try:
                header = next(csv_reader)
            except StopIteration:
                logger.error("Пустой CSV файл.")
                import_csv_element.status = False
                import_csv_element.save()
                return

            required_headers = ["id", "type", "image", "slug", "site"]
            missing_headers = [h for h in required_headers if h not in header]
            if missing_headers:
                logger.error(f"Отсутствуют необходимые заголовки: {missing_headers}")
                import_csv_element.status = False
                import_csv_element.save()
                return

            optional_headers = []

            passed_count = 0
            banners = []

            for row in csv_reader:
                try:
                    banner_data = {}
                    for field in required_headers + optional_headers:
                        if field in header:
                            banner_data[field] = row[header.index(field)].strip()
                        else:
                            banner_data[field] = None

                    try:
                        banner_data["image"] = download_image(banner_data["image"])
                        if banner_data["image"] is None:
                            logger.warning(
                                f"Не удалось загрузить изображение: {banner_data['image']}"
                            )
                    except Exception as e:
                        logger.warning(f"Ошибка при загрузке изображения: {e}")
                        banner_data["image"] = None

                    site_ids = banner_data["site"].split(",")
                    sites = []
                    for site_id in site_ids:
                        try:
                            site = Site.objects.get(id=site_id.strip())
                            sites.append(site)
                        except ObjectDoesNotExist:
                            logger.warning(f"Сайт с ID {site_id} не найден. Пропущено.")

                    banner, created = Banner.objects.get_or_create(
                        id=banner_data["id"],
                        defaults={
                            "type": banner_data["type"],
                            "image": banner_data["image"],
                            "slug": banner_data["slug"],
                        },
                    )
                    if created:
                        import_csv_element.added_element += 1
                        import_csv_element.save()
                    else:
                        import_csv_element.upload_element += 1
                        import_csv_element.save()
                    banners.append((banner, created))

                    if created:
                        logger.info(f"Создан новый баннер: {banner_data['id']}")
                    else:
                        logger.info(
                            f"Обновлен существующий баннер: {banner_data['id']}"
                        )
                        banner.type = banner_data["type"]
                        banner.image = banner_data["image"]
                        banner.slug = banner_data["slug"]
                        banner.save()

                    banner.site.set(sites)

                    import_csv_element.passed += 1
                    import_csv_element.save()

                    import_csv.passed = import_csv.elements.aggregate(Sum("passed"))[
                        "passed__sum"
                    ]
                    import_csv.added_element = import_csv.elements.aggregate(
                        Sum("added_element")
                    )["added_element__sum"]
                    import_csv.upload_element = import_csv.elements.aggregate(
                        Sum("upload_element")
                    )["upload_element__sum"]
                    import_csv.save()

                except (IndexError, ValueError) as e:
                    logger.error(f"Ошибка при обработке строки: {e}")
                except Exception as e:
                    logger.error(f"Произошла ошибка: {e}", exc_info=True)

            import_csv_element.status = True
            import_csv_element.save()

            all_elements_have_status = (
                import_csv.elements.all().aggregate(all_status_true=Sum("status"))[
                    "all_status_true"
                ]
                == import_csv.elements.count()
            )
            if all_elements_have_status:
                import_csv.status = True
                import_csv.elements.all().delete()
                import_csv.save()

        except Exception as e:
            import_csv_element.status = False
            import_csv_element.save()
            logger.error(f"Произошла ошибка при обработке CSV: {e}", exc_info=True)

    process_csv()

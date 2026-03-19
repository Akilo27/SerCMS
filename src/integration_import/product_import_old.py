import os
import threading
import logging
import csv
import requests
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from shop.models import (
    Products,
    Categories,
    Manufacturers,
    ProductsGallery,
)
from .models import ImportCsv
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
import validators

logger = logging.getLogger(__name__)


def download_image(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    content_type = response.headers.get("Content-Type", "")
    if "image" not in content_type:
        return None

    # Получаем оригинальное имя файла из URL-адреса
    original_filename = os.path.basename(image_url.split("?")[0])

    file_extension = content_type.split("/")[-1]
    if file_extension.lower() != original_filename.split(".")[-1].lower():
        # Если расширение файла из Content-Type не совпадает с расширением в оригинальном имени файла,
        # используем расширение из оригинального имени файла
        original_extension = original_filename.split(".")[-1]
        file_extension = original_extension

    return ContentFile(response.content, name=original_filename)


def to_boolean(value):
    if value == "1":
        return True
    elif value == "0":
        return False
    return False


def process_product_csv(csv_file, request):
    def process_csv(import_csv_instance):
        try:
            csv_file.seek(0)
            data_set = csv_file.read().decode("UTF-8")
            csv_reader = csv.reader(data_set.splitlines(), delimiter=",")

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

            passed_count = 0
            added_count = 0
            updated_count = 0

            for row in csv_reader:
                try:
                    product_data = {
                        field: row[header.index(field)].strip()
                        if field in header
                        else None
                        for field in required_headers + optional_headers
                    }

                    if product_data["slug"] and "%" in product_data["slug"]:
                        messages.info(
                            request, "Значение 'slug' содержит '%', оставляем пустым."
                        )
                        product_data["slug"] = ""

                    product_data["price"] = float(product_data["price"])
                    product_data["order"] = to_boolean(product_data["order"])
                    product_data["review"] = to_boolean(product_data["review"])
                    product_data["faqs"] = to_boolean(product_data["faqs"])
                    product_data["comment"] = to_boolean(
                        product_data.get("comment", "0")
                    )

                    try:
                        product_data["image_content"] = download_image(
                            product_data["image"]
                        )
                        if product_data["image_content"] is None:
                            messages.warning(
                                request,
                                f"Не удалось загрузить изображение: {product_data['image']}",
                            )
                    except Exception as e:
                        messages.warning(
                            request, f"Ошибка при загрузке изображения: {e}"
                        )
                        product_data["image_content"] = None

                    sites = []
                    for site_id in product_data["site"].split(","):
                        try:
                            site = Site.objects.get(id=site_id.strip())
                            sites.append(site)
                        except ObjectDoesNotExist:
                            messages.warning(
                                request, f"Сайт с ID {site_id} не найден. Пропущено."
                            )

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

                    product, product_created = Products.objects.update_or_create(
                        manufacturer_identifier=product_data["id"],
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
                        },
                    )

                    if product_created:
                        messages.info(
                            request, f"Создан новый продукт: {product_data['id']}"
                        )
                        added_count += 1
                    else:
                        messages.info(
                            request,
                            f"Обновлен существующий продукт: {product_data['id']}",
                        )
                        updated_count += 1

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
                            except Exception as e:
                                messages.warning(
                                    request,
                                    f"Ошибка при загрузке изображения из галереи: {e}",
                                )

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
                                messages.warning(
                                    request,
                                    f"Неверный формат данных или склад с ID {storage_id} не найден: {pair}. Пропущено.",
                                )

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
                                messages.warning(
                                    request,
                                    f"Неверный формат данных или склад с ID {storage_id} не найден: {pair}. Пропущено.",
                                )

                    passed_count += 1

                except (IndexError, ValueError) as e:
                    messages.error(request, f"Ошибка при обработке строки: {e}")
                except Exception as e:
                    messages.error(request, f"Произошла ошибка: {e}")
                    logger.error(f"Произошла ошибка: {e}", exc_info=True)

                import_csv_instance.passed = passed_count
                import_csv_instance.added_element = added_count
                import_csv_instance.upload_element = updated_count
                import_csv_instance.save()

        except Exception as e:
            messages.error(request, f"Ошибка при обработке CSV: {e}")
            import_csv_instance.status = False
            import_csv_instance.save()

    import_csv_instance = ImportCsv.objects.create(
        type=1,
        status=True,
        quantity=0,
        added_element=0,
        upload_element=0,
        passed=0,
        file=csv_file.name,
    )

    try:
        csv_file.seek(0)
        data_set = csv_file.read().decode("UTF-8")
        csv_reader = csv.reader(data_set.splitlines(), delimiter=",")
        row_count = sum(1 for _ in csv_reader) - 1
        import_csv_instance.quantity = row_count
        import_csv_instance.save()

        thread = threading.Thread(target=process_csv, args=(import_csv_instance,))
        thread.start()

    except Exception as e:
        messages.error(request, f"Ошибка при чтении CSV: {e}")
        import_csv_instance.status = False
        import_csv_instance.save()


def process_category_csv(csv_file, request):
    def process_csv(import_csv):
        csv_file.seek(0)
        data_set = csv_file.read().decode("UTF-8")
        csv_reader = csv.reader(data_set.splitlines(), delimiter=",")
        try:
            header = next(csv_reader)
        except StopIteration:
            messages.error(request, "Пустой CSV файл.")
            import_csv.status = False
            import_csv.save()
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
            messages.error(
                request, f"Отсутствуют необходимые заголовки: {missing_headers}"
            )
            import_csv.status = False
            import_csv.save()
            return

        passed_count = 0
        categories = []

        for row in csv_reader:
            try:
                category_data = {
                    field: row[header.index(field)].strip() if field in header else None
                    for field in required_headers
                }

                # Получение сайтов
                site_ids = category_data["site"].split(",")
                sites = []
                for site_id in site_ids:
                    try:
                        site = Site.objects.get(id=site_id.strip())
                        sites.append(site)
                    except ObjectDoesNotExist:
                        messages.warning(
                            request, f"Сайт с ID {site_id} не найден. Пропущено."
                        )

                # Получение родительской категории
                parent_category = None
                parent_id = category_data.get("parent")
                if parent_id:
                    try:
                        parent_category = Categorys.objects.get(id=parent_id.strip())
                    except Categorys.DoesNotExist:
                        messages.warning(
                            request,
                            f"Родительская категория с ID {parent_id} не найдена. Пропущено.",
                        )

                # Загрузка изображений
                for field in ["cover", "icon", "image"]:
                    if field not in category_data or not category_data[field]:
                        continue
                    image_url = category_data[field]
                    if not validators.url(image_url):
                        messages.warning(
                            request, f"Неверный URL изображения ({field}): {image_url}"
                        )
                        continue  # Skip processing this row
                    try:
                        image_content = download_image(image_url)
                        if image_content is None:
                            messages.warning(
                                request,
                                f"Не удалось загрузить изображение ({field}): {image_url}",
                            )
                            continue
                    except Exception as e:
                        messages.warning(
                            request, f"Ошибка при загрузке изображения ({field}): {e}"
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
                category, created = Categorys.objects.update_or_create(
                    id=category_data["id"], defaults=category_defaults
                )

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

                passed_count += 1
                if created:
                    messages.info(
                        request, f"Создана новая категория: {category_data['id']}"
                    )
                else:
                    messages.info(
                        request,
                        f"Обновлена существующая категория: {category_data['id']}",
                    )
            except (IndexError, ValueError) as e:
                messages.error(request, f"Ошибка при обработке строки: {e}")
                logger.error(f"Ошибка при обработке строки: {e}", exc_info=True)
            except Exception as e:
                messages.error(request, f"Произошла ошибка: {e}")
                logger.error(f"Произошла ошибка: {e}", exc_info=True)

        # Обновить поле added_element и upload_element в экземпляре import_csv после обработки
        import_csv.added_element = sum(
            1 for _, created in categories if created
        )  # количество созданных категорий
        import_csv.upload_element = sum(
            1 for _, created in categories if not created
        )  # количество обновленных категорий
        import_csv.passed = passed_count
        import_csv.save()

    # Создать экземпляр модели ImportCsv
    import_csv = ImportCsv.objects.create(
        type=2,  # Измените это значение в зависимости от выбранного типа импорта
        status=True,
        quantity=0,  # Это будет обновлено позже
        added_element=0,  # Созданные
        upload_element=0,  # Обновленные
        passed=0,
        file=csv_file.name,  # Предполагается, что это поле файла, где хранится CSV файл
    )

    # Обновить количество строк в импортируемом файле
    csv_file.seek(0)
    data_set = csv_file.read().decode("UTF-8")
    csv_reader = csv.reader(data_set.splitlines(), delimiter=",")
    row_count = sum(1 for row in csv_reader) - 1
    # Создание экземпляра ImportCsv завершено, обновляем quantity
    import_csv.quantity = row_count
    import_csv.save()

    # Запуск обработки CSV в отдельном потоке
    thread = threading.Thread(target=process_csv, args=(import_csv,))
    thread.start()


def process_categories_csv(csv_file, request):
    def process_csv(import_csv):
        csv_file.seek(0)
        data_set = csv_file.read().decode("UTF-8")
        csv_reader = csv.reader(data_set.splitlines(), delimiter=",")
        try:
            header = next(csv_reader)
        except StopIteration:
            messages.error(request, "Пустой CSV файл.")
            import_csv.status = False
            import_csv.save()
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
            messages.error(
                request, f"Отсутствуют необходимые заголовки: {missing_headers}"
            )
            import_csv.status = False
            import_csv.save()
            return

        passed_count = 0
        categories = []

        for row in csv_reader:
            try:
                category_data = {
                    field: row[header.index(field)].strip() if field in header else None
                    for field in required_headers
                }

                # Получение сайтов
                site_ids = category_data["site"].split(",")
                sites = []
                for site_id in site_ids:
                    try:
                        site = Site.objects.get(id=site_id.strip())
                        sites.append(site)
                    except ObjectDoesNotExist:
                        messages.warning(
                            request, f"Сайт с ID {site_id} не найден. Пропущено."
                        )

                # Получение родительской категории
                parent_category = None
                parent_id = category_data.get("parent")
                if parent_id:
                    try:
                        parent_category = Categories.objects.get(id=parent_id.strip())
                    except Categories.DoesNotExist:
                        messages.warning(
                            request,
                            f"Родительская категория с ID {parent_id} не найдена. Пропущено.",
                        )

                # Загрузка изображений
                for field in ["cover", "icon", "image"]:
                    if field not in category_data or not category_data[field]:
                        continue
                    image_url = category_data[field]
                    if not validators.url(image_url):
                        messages.warning(
                            request, f"Неверный URL изображения ({field}): {image_url}"
                        )
                        continue  # Skip processing this row
                    try:
                        image_content = download_image(image_url)
                        if image_content is None:
                            messages.warning(
                                request,
                                f"Не удалось загрузить изображение ({field}): {image_url}",
                            )
                            continue
                    except Exception as e:
                        messages.warning(
                            request, f"Ошибка при загрузке изображения ({field}): {e}"
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

                passed_count += 1
                if created:
                    messages.info(
                        request, f"Создана новая категория: {category_data['id']}"
                    )
                else:
                    messages.info(
                        request,
                        f"Обновлена существующая категория: {category_data['id']}",
                    )
            except (IndexError, ValueError) as e:
                messages.error(request, f"Ошибка при обработке строки: {e}")
                logger.error(f"Ошибка при обработке строки: {e}", exc_info=True)
            except Exception as e:
                messages.error(request, f"Произошла ошибка: {e}")
                logger.error(f"Произошла ошибка: {e}", exc_info=True)

        # Обновить поле added_element и upload_element в экземпляре import_csv после обработки
        import_csv.added_element = sum(
            1 for _, created in categories if created
        )  # количество созданных категорий
        import_csv.upload_element = sum(
            1 for _, created in categories if not created
        )  # количество обновленных категорий
        import_csv.passed = passed_count
        import_csv.save()

    # Создать экземпляр модели ImportCsv
    import_csv = ImportCsv.objects.create(
        type=2,  # Измените это значение в зависимости от выбранного типа импорта
        status=True,
        quantity=0,  # Это будет обновлено позже
        added_element=0,  # Созданные
        upload_element=0,  # Обновленные
        passed=0,
        file=csv_file.name,  # Предполагается, что это поле файла, где хранится CSV файл
    )

    # Обновить количество строк в импортируемом файле
    csv_file.seek(0)
    data_set = csv_file.read().decode("UTF-8")
    csv_reader = csv.reader(data_set.splitlines(), delimiter=",")
    row_count = sum(1 for row in csv_reader) - 1
    # Создание экземпляра ImportCsv завершено, обновляем quantity
    import_csv.quantity = row_count
    import_csv.save()

    # Запуск обработки CSV в отдельном потоке
    thread = threading.Thread(target=process_csv, args=(import_csv,))
    thread.start()


def process_manufacturer_csv(csv_file, request):
    def process_csv(import_csv):
        csv_file.seek(0)
        data_set = csv_file.read().decode("UTF-8")
        csv_reader = csv.reader(data_set.splitlines(), delimiter=",")
        try:
            header = next(csv_reader)
        except StopIteration:
            messages.error(request, "Пустой CSV файл.")
            import_csv.status = False
            import_csv.save()
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
            messages.error(
                request, f"Отсутствуют необходимые заголовки: {missing_headers}"
            )
            import_csv.status = False
            import_csv.save()
            return

        passed_count = 0
        manufacturers = []

        for row in csv_reader:
            try:
                manufacturer_data = {
                    field: row[header.index(field)].strip() if field in header else None
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
                        messages.warning(
                            request, f"Сайт с ID {site_id} не найден. Пропущено."
                        )

                # Загрузка изображений
                for field in ["cover", "image"]:
                    if field not in manufacturer_data or not manufacturer_data[field]:
                        continue
                    image_url = manufacturer_data[field]
                    if not validators.url(image_url):
                        messages.warning(
                            request, f"Неверный URL изображения ({field}): {image_url}"
                        )
                        continue
                    try:
                        image_content = download_image(image_url)
                        if image_content is None:
                            messages.warning(
                                request,
                                f"Не удалось загрузить изображение ({field}): {image_url}",
                            )
                            continue
                    except Exception as e:
                        messages.warning(
                            request, f"Ошибка при загрузке изображения ({field}): {e}"
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

                passed_count += 1
                if created:
                    messages.info(
                        request,
                        f"Создан новый производитель: {manufacturer_data['id']}",
                    )
                else:
                    messages.info(
                        request,
                        f"Обновлен существующий производитель: {manufacturer_data['id']}",
                    )
            except (IndexError, ValueError) as e:
                messages.error(request, f"Ошибка при обработке строки: {e}")
                logger.error(f"Ошибка при обработке строки: {e}", exc_info=True)
            except Exception as e:
                messages.error(request, f"Произошла ошибка: {e}")
                logger.error(f"Произошла ошибка: {e}", exc_info=True)

        # Обновление поля added_element и upload_element в экземпляре import_csv после обработки
        import_csv.added_element = sum(
            1 for _, created in manufacturers if created
        )  # количество созданных производителей
        import_csv.upload_element = sum(
            1 for _, created in manufacturers if created
        )  # количество обновленных производителей
        import_csv.passed = passed_count
        import_csv.save()

    # Создание экземпляра модели ImportCsv
    import_csv = ImportCsv.objects.create(
        type=3,  # Измените это значение в зависимости от выбранного типа импорта
        status=True,
        quantity=0,  # Это будет обновлено позже
        added_element=0,  # Созданные
        upload_element=0,  # Обновленные
        passed=0,
        file=csv_file.name,  # Предполагается, что это поле файла, где хранится CSV файл
    )

    # Обновление количества строк в импортируемом файле
    csv_file.seek(0)
    data_set = csv_file.read().decode("UTF-8")
    csv_reader = csv.reader(data_set.splitlines(), delimiter=",")
    row_count = sum(1 for row in csv_reader) - 1
    import_csv.quantity = row_count
    import_csv.save()

    # Запуск обработки CSV в отдельном потоке
    thread = threading.Thread(target=process_csv, args=(import_csv,))
    thread.start()


def process_blog_csv(csv_file, request):
    def process_csv(import_csv):
        csv_file.seek(0)
        data_set = csv_file.read().decode("UTF-8")
        csv_reader = csv.reader(data_set.splitlines(), delimiter=",")

        try:
            header = next(csv_reader)
        except StopIteration:
            messages.error(request, "Пустой CSV файл.")
            import_csv.status = False
            import_csv.save()
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
            messages.error(
                request, f"Отсутствуют необходимые заголовки: {missing_headers}"
            )
            import_csv.status = False
            import_csv.save()
            return

        optional_headers = []

        passed_count = (
            0  # Переменная для подсчета успешно созданных или обновленных продуктов
        )

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
                    messages.info(
                        request, "Значение 'slug' содержит '%', оставляем пустым."
                    )
                    blogs_data["slug"] = ""

                try:
                    blogs_data["image_content"] = download_image(blogs_data["cover"])
                    if blogs_data["image_content"] is None:
                        messages.warning(
                            request,
                            f"Не удалось загрузить изображение: {blogs_data['cover']}",
                        )
                except Exception as e:
                    messages.warning(request, f"Ошибка при загрузке изображения: {e}")
                    blogs_data["image_content"] = None

                try:
                    blogs_data["previev_content"] = download_image(
                        blogs_data["previev"]
                    )
                    if blogs_data["previev_content"] is None:
                        messages.warning(
                            request,
                            f"Не удалось загрузить изображение: {blogs_data['previev']}",
                        )
                except Exception as e:
                    messages.warning(request, f"Ошибка при загрузке изображения: {e}")
                    blogs_data["previev_content"] = None

                site_ids = blogs_data["site"].split(",")
                sites = []
                for site_id in site_ids:
                    try:
                        site = Site.objects.get(id=site_id.strip())
                        sites.append(site)
                    except ObjectDoesNotExist:
                        messages.warning(
                            request, f"Сайт с ID {site_id} не найден. Пропущено."
                        )

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
                # Сохраняем информацию о продукте (blogs, created) в списке blogss
                blogss.append((blogs, created))

                if created:
                    messages.info(request, f"Создан новый продукт: {blogs_data['id']}")
                else:
                    messages.info(
                        request, f"Обновлен существующий продукт: {blogs_data['id']}"
                    )
                    # Если продукт уже существует, обновите поля
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

                passed_count += (
                    1  # Увеличить счетчик успешно созданных или обновленных продуктов
                )

            except (IndexError, ValueError) as e:
                messages.error(request, f"Ошибка при обработке строки: {e}")
            except Exception as e:
                messages.error(request, f"Произошла ошибка: {e}")
                logger.error(f"Произошла ошибка: {e}", exc_info=True)

                # Обновить поле passed в экземпляре import_csv после обработки
            import_csv.passed = passed_count
            import_csv.added_element = sum(
                1 for _, created in blogss if created
            )  # количество созданных продуктов
            import_csv.upload_element = sum(
                1 for _, created in blogss if not created
            )  # количество обновленных продуктов
            import_csv.save()

            # Создать экземпляр модели ImportCsv

    import_csv = ImportCsv.objects.create(
        type=1,  # Измените это значение в зависимости от выбранного типа импорта
        status=True,
        quantity=0,  # Это будет обновлено позже
        added_element=0,  # Созданные
        upload_element=0,  # Обновленные
        passed=0,
        file=csv_file.name,  # Предполагается, что это поле файла, где хранится CSV файл
    )

    # Обновить количество строк в импортируемом файле
    csv_file.seek(0)
    data_set = csv_file.read().decode("UTF-8")
    csv_reader = csv.reader(data_set.splitlines(), delimiter=",")
    row_count = sum(1 for row in csv_reader) - 1
    # Создание экземпляра ImportCsv завершено, обновляем quantity
    import_csv.quantity = row_count
    import_csv.save()

    # Запуск обработки CSV в отдельном потоке
    thread = threading.Thread(target=process_csv, args=(import_csv,))
    thread.start()


def process_seo_csv(csv_file, request):
    def process_csv(import_csv):
        csv_file.seek(0)
        data_set = csv_file.read().decode("UTF-8")
        csv_reader = csv.reader(data_set.splitlines(), delimiter=",")

        try:
            header = next(csv_reader)
        except StopIteration:
            messages.error(request, "Пустой CSV файл.")
            import_csv.status = False
            import_csv.save()
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
            messages.error(
                request, f"Отсутствуют необходимые заголовки: {missing_headers}"
            )
            import_csv.status = False
            import_csv.save()
            return

        optional_headers = []

        passed_count = (
            0  # Переменная для подсчета успешно созданных или обновленных продуктов
        )

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
                    seo_data["previev_content"] = download_image(seo_data["previev"])
                    if seo_data["previev_content"] is None:
                        messages.warning(
                            request,
                            f"Не удалось загрузить изображение: {seo_data['previev']}",
                        )
                except Exception as e:
                    messages.warning(request, f"Ошибка при загрузке изображения: {e}")
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
                # Сохраняем информацию о продукте (seo, created) в списке seos
                seos.append((seo, created))

                if created:
                    messages.info(request, f"Создан новый продукт: {seo_data['id']}")
                else:
                    messages.info(
                        request, f"Обновлен существующий продукт: {seo_data['id']}"
                    )
                    # Если продукт уже существует, обновите поля
                    seo.pagetype = seo_data["pagetype"]
                    seo.setting = settings_globale
                    seo.previev = seo_data["previev_content"]
                    seo.title = seo_data["title"]
                    seo.description = seo_data["description"]
                    seo.propertytitle = seo_data["propertytitle"]
                    seo.propertydescription = seo_data["propertydescription"]
                    seo.save()

                passed_count += (
                    1  # Увеличить счетчик успешно созданных или обновленных продуктов
                )

            except (IndexError, ValueError) as e:
                messages.error(request, f"Ошибка при обработке строки: {e}")
                print(f"Ошибка при обработке строки: {e}")  # Печать ошибки
            except Exception as e:
                messages.error(request, f"Произошла ошибка: {e}")
                logger.error(f"Произошла ошибка: {e}", exc_info=True)
                print(f"Произошла ошибка: {e}")  # Печать ошибки

            # Обновить поле passed в экземпляре import_csv после обработки
            import_csv.passed = passed_count
            import_csv.added_element = sum(
                1 for _, created in seos if created
            )  # количество созданных продуктов
            import_csv.upload_element = sum(
                1 for _, created in seos if not created
            )  # количество обновленных продуктов
            import_csv.save()

    import_csv = ImportCsv.objects.create(
        type=7,  # Измените это значение в зависимости от выбранного типа импорта
        status=True,
        quantity=0,  # Это будет обновлено позже
        added_element=0,  # Созданные
        upload_element=0,  # Обновленные
        passed=0,
        file=csv_file.name,  # Предполагается, что это поле файла, где хранится CSV файл
    )

    # Обновить количество строк в импортируемом файле
    csv_file.seek(0)
    data_set = csv_file.read().decode("UTF-8")
    csv_reader = csv.reader(data_set.splitlines(), delimiter=",")
    row_count = sum(1 for row in csv_reader) - 1
    # Создание экземпляра ImportCsv завершено, обновляем quantity
    import_csv.quantity = row_count
    import_csv.save()

    # Запуск обработки CSV в отдельном потоке
    thread = threading.Thread(target=process_csv, args=(import_csv,))
    thread.start()


def process_banner_csv(csv_file, request):
    def process_csv(import_csv):
        csv_file.seek(0)
        data_set = csv_file.read().decode("UTF-8")
        csv_reader = csv.reader(data_set.splitlines(), delimiter=",")

        try:
            header = next(csv_reader)
        except StopIteration:
            messages.error(request, "Пустой CSV файл.")
            import_csv.status = False
            import_csv.save()
            return

        required_headers = ["id", "type", "image", "slug", "site"]
        missing_headers = [h for h in required_headers if h not in header]
        if missing_headers:
            messages.error(
                request, f"Отсутствуют необходимые заголовки: {missing_headers}"
            )
            import_csv.status = False
            import_csv.save()
            return

        optional_headers = []

        passed_count = (
            0  # Переменная для подсчета успешно созданных или обновленных продуктов
        )

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
                        messages.warning(
                            request,
                            f"Не удалось загрузить изображение: {banner_data['image']}",
                        )
                except Exception as e:
                    messages.warning(request, f"Ошибка при загрузке изображения: {e}")
                    banner_data["image"] = None

                site_ids = banner_data["site"].split(",")
                sites = []
                for site_id in site_ids:
                    try:
                        site = Site.objects.get(id=site_id.strip())
                        sites.append(site)
                    except ObjectDoesNotExist:
                        messages.warning(
                            request, f"Сайт с ID {site_id} не найден. Пропущено."
                        )

                banner, created = Banner.objects.get_or_create(
                    id=banner_data["id"],
                    defaults={
                        "type": banner_data["type"],
                        "image": banner_data["image"],
                        "slug": banner_data["slug"],
                    },
                )
                # Сохраняем информацию о продукте (banner, created) в списке banners
                banners.append((banner, created))

                if created:
                    messages.info(request, f"Создан новый продукт: {banner_data['id']}")
                else:
                    messages.info(
                        request, f"Обновлен существующий продукт: {banner_data['id']}"
                    )
                    # Если продукт уже существует, обновите поля
                    banner.type = banner_data["type"]
                    banner.image = banner_data["image"]
                    banner.slug = banner_data["slug"]
                    banner.save()

                banner.site.set(sites)

                passed_count += (
                    1  # Увеличить счетчик успешно созданных или обновленных продуктов
                )

            except (IndexError, ValueError) as e:
                messages.error(request, f"Ошибка при обработке строки: {e}")
                print(f"Ошибка при обработке строки: {e}")  # Печать ошибки
            except Exception as e:
                messages.error(request, f"Произошла ошибка: {e}")
                logger.error(f"Произошла ошибка: {e}", exc_info=True)
                print(f"Произошла ошибка: {e}")  # Печать ошибки

            # Обновить поле passed в экземпляре import_csv после обработки
            import_csv.passed = passed_count
            import_csv.added_element = sum(
                1 for _, created in banners if created
            )  # количество созданных продуктов
            import_csv.upload_element = sum(
                1 for _, created in banners if not created
            )  # количество обновленных продуктов
            import_csv.save()

        # Создать экземпляр модели ImportCsv

    import_csv = ImportCsv.objects.create(
        type=7,  # Измените это значение в зависимости от выбранного типа импорта
        status=True,
        quantity=0,  # Это будет обновлено позже
        added_element=0,  # Созданные
        upload_element=0,  # Обновленные
        passed=0,
        file=csv_file.name,  # Предполагается, что это поле файла, где хранится CSV файл
    )

    # Обновить количество строк в импортируемом файле
    csv_file.seek(0)
    data_set = csv_file.read().decode("UTF-8")
    csv_reader = csv.reader(data_set.splitlines(), delimiter=",")
    row_count = sum(1 for row in csv_reader) - 1
    # Создание экземпляра ImportCsv завершено, обновляем quantity
    import_csv.quantity = row_count
    import_csv.save()

    # Запуск обработки CSV в отдельном потоке
    thread = threading.Thread(target=process_csv, args=(import_csv,))
    thread.start()

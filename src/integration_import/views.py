# from lib2to3.fixes.fix_input import context

import openpyxl
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView

from integration_import.forms import CSVUploadForm
from django.views.generic.edit import FormView
from django.utils.decorators import method_decorator
from integration_import.models import (
    ImportCsv,
    UploadFromDiskImportCsv,
)
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib import messages
from django.db import IntegrityError

from .tasks import download_file_from_model, delete_import_from_db
from django.http import JsonResponse


# Проверка, что пользователь - администратор (статус `is_staff`)
def is_admin(user):
    return user.is_staff  # Или user.is_superuser


@method_decorator(user_passes_test(is_admin), name="dispatch")
class UploadCSVView(FormView):
    template_name = "upload_csv.html"
    form_class = CSVUploadForm  # Убедитесь, что эта форма поддерживает XLSX файлы
    success_url = "/upload-csv/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pagination setup
        import_csv_list = ImportCsv.objects.all().order_by("-create")
        paginator = Paginator(import_csv_list, 10)
        page = self.request.GET.get("page")
        try:
            import_csv = paginator.page(page)
        except PageNotAnInteger:
            import_csv = paginator.page(1)
        except EmptyPage:
            import_csv = paginator.page(paginator.num_pages)
        context["import_csv"] = import_csv
        return context

    def form_valid(self, form):
        xlsx_file = form.cleaned_data["csv_file"]
        import_type = self.request.POST.get("import_type")
        user = self.request.user

        if not xlsx_file.name.endswith(".xlsx"):
            messages.error(self.request, "Это не файл XLSX.")
            return self.form_invalid(form)

        type_mapping = {
            "products": 1,
            "categories": 2,
            "variable": 3,
            "manufacturers": 4,
            "blogs": 5,
            "categorys": 6,
            "seo": 7,
            "banner": 9,
            "settingsglobale": 8,
        }
        whats_type = type_mapping.get(import_type, 1)

        try:
            # Чтение файла без `seek(0)`
            workbook = openpyxl.load_workbook(xlsx_file, data_only=True)
            sheet = workbook.active
            row_count = sheet.max_row - 1  # Вычитание 1 для исключения заголовка

        except Exception:
            messages.error(self.request, "Ошибка при чтении файла XLSX.")
            return self.form_invalid(form)

        try:
            imports_xlsx = ImportCsv.objects.create(
                user=user,
                type=whats_type,
                status=False,
                quantity=row_count,
                added_element=0,
                upload_element=0,
                passed=0,
                file=xlsx_file,
            )
            messages.success(self.request, "Файл начал обработку в фоновом режиме.")
        except IntegrityError as e:
            if "duplicate key value violates unique constraint" in str(e):
                pass
            else:
                # Обработка других ошибок
                messages.error(self.request, f"Ошибка: {e}")
        except Exception as e:
            # Обработка остальных исключений
            messages.error(self.request, f"Ошибка: {e}")
        return super().form_valid(form)


def manual_download(request, upload_id):
    if request.method == "POST":
        try:
            upload = UploadFromDiskImportCsv.objects.get(id=upload_id)
            download_file_from_model.delay(upload.type, 2)
            return JsonResponse({"status": "Скачивание начато."}, status=202)
        except Exception as e:
            return JsonResponse({"error": f"Ошибка: {e}"}, status=400)
    return JsonResponse({"error": "Неверный метод запроса."}, status=405)


def manual_delete(request, importcsv_id):
    if request.method == "POST":
        if request.user.is_staff:
            try:
                try:
                    importcsv = ImportCsv.objects.get(
                        user=request.user, id=importcsv_id
                    )
                except ObjectDoesNotExist:
                    importcsv = ImportCsv.objects.get(id=importcsv_id)
                delete_import_from_db.delay(importcsv.id)
                return JsonResponse({"status": "Удаление начато."}, status=202)
            except Exception as e:
                return JsonResponse({"error": f"Ошибка: {e}"}, status=400)
        else:
            return JsonResponse({"error": "Не авторизован ."}, status=429)
    return JsonResponse({"error": "Неверный метод запроса."}, status=405)


def pause_switch_in_importcsv(request, importcsv_id):
    if request.method == "POST":
        if request.user.is_staff:
            try:
                try:
                    importcsv = ImportCsv.objects.get(
                        user=request.user, id=importcsv_id
                    )
                except ObjectDoesNotExist:
                    importcsv = ImportCsv.objects.get(id=importcsv_id)
                pausestatus = request.POST.get("pausestatus")
                if pausestatus == "pause":
                    importcsv.pause_status = True
                    return JsonResponse(
                        {"status": "загрузка поставлена на паузу", "type": "pause"},
                        status=202,
                    )
                elif pausestatus == "continue":
                    importcsv.pause_status = False
                    return JsonResponse(
                        {"status": "загрузка продолжается", "type": "continue"},
                        status=202,
                    )

            except Exception as e:
                return JsonResponse({"error": f"Ошибка: {e}"}, status=400)
        else:
            return JsonResponse({"error": "Не авторизован ."}, status=429)
    return JsonResponse({"error": "Неверный метод запроса."}, status=405)


@method_decorator(user_passes_test(is_admin), name="dispatch")
class UploadFromDiskCSVView(TemplateView):
    template_name = "upload_from_disk.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        content = UploadFromDiskImportCsv.objects.all()

        context["content"] = content
        return context

from django.contrib import admin
from integration_import.models import (
    ImportCsv,
    ImportCsvElement,
    UploadFromDiskImportCsv,
    YandexDiskIntegration,
)

# Register your models here.
admin.site.register(ImportCsv)
admin.site.register(UploadFromDiskImportCsv)
admin.site.register(YandexDiskIntegration)


@admin.register(ImportCsvElement)
class ImportCsvElementAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "file",
        "status",
        "passed",
        "added_element",
        "upload_element",
        "quantity",
    ]

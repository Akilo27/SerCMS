from django.apps import AppConfig


class IntegrationImportConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "integration_import"
    verbose_name = "Импорт"
    verbose_name_plural = "Импорты"

    def ready(self):
        pass

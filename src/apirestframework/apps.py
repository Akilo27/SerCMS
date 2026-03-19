from django.apps import AppConfig


class ApirestframeworkConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apirestframework"

    def ready(self):
        pass

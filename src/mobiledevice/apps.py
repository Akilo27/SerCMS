from django.apps import AppConfig


class MobiledeviceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mobiledevice"

    def ready(self):
        pass

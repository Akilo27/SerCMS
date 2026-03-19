from django.apps import AppConfig



class LoyaltyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "loyalty"
    verbose_name = "Лояльность"
    verbose_name_plural = "Лояльности"

    def ready(self):
        pass

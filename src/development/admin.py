from django.contrib import admin
from .models import *


# Register your models here.
@admin.register(ThemesCastegorys)
class ThemesCastegorysAdmin(admin.ModelAdmin):
    model = ThemesCastegorys


@admin.register(Themes)
class ThemesAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "slug"]

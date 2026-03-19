from django.contrib import admin
from .models import *


# Register your models here.
@admin.register(Documentations)
class DocumentationsAdmin(admin.ModelAdmin):
    model = Documentations


@admin.register(DocumentationsMedia)
class DocumentationsMediaAdmin(admin.ModelAdmin):
    model = DocumentationsMedia

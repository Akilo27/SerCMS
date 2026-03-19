from django.contrib import admin
from .models import *


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "client", "amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("created_at",)


@admin.register(StatusPayment)
class StatusPaymentAdmin(admin.ModelAdmin):
    list_display = ("amount", "description")


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ("title", "stage", "expected_close_date", "created_at")
    list_filter = ("stage", "expected_close_date")
    search_fields = ("title",)
    readonly_fields = ("created_at",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "assigned_to", "type", "due_date")
    list_filter = ("type",)
    search_fields = ("title", "notes")


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("author", "content", "created_at")
    list_filter = ("created_at",)
    search_fields = ("content",)


@admin.register(Leaddocement)
class LeaddocementAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "lead", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title",)

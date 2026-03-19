from django.contrib import admin
from .models import *

# Register your models here.


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    model = Schedule


@admin.register(VacancyResponse)
class VacancyResponseAdmin(admin.ModelAdmin):
    model = VacancyResponse


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "posted_at", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "description")

admin.site.register(HRChangeLog)
admin.site.register(Lesson)
admin.site.register(LessonMaterial)
admin.site.register(TestResult)
admin.site.register(WorkShift)

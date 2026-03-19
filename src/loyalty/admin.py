from django.contrib import admin
from .models import PersonalPromotion

class PersonalPromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_active', 'created_at', 'valid_until')
    list_filter = ('is_active', 'created_at', 'category', 'brand')
    search_fields = ('name', 'description', 'user__user__username')  # предположим, что у Profile есть связанный user
    list_editable = ('is_active',)
    ordering = ('-created_at',)
    # Можно добавить поля для фильтрации или поиска по другим параметрам по необходимости

admin.site.register(PersonalPromotion, PersonalPromotionAdmin)
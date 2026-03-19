from django.contrib import admin
import nested_admin
from moderation.models import ReklamBanner
from .models import *
from django.urls import path
from django.template.response import TemplateResponse
from django import forms
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.shortcuts import redirect
from django.contrib.admin import SimpleListFilter
from django.shortcuts import render, redirect
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME

class ImageStatusFilter(SimpleListFilter):
    title = "Изображение"
    parameter_name = "has_image"

    def lookups(self, request, model_admin):
        return (
            ("default", "С дефолтным изображением"),
            ("custom", "С кастомным изображением"),
        )

    def queryset(self, request, queryset):
        if self.value() == "default":
            return queryset.filter(image="default/product-nophoto.png")
        if self.value() == "custom":
            return queryset.exclude(image="default/product-nophoto.png")
        return queryset


class ChangeParentForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    parent = forms.ModelChoiceField(
        queryset=Categories.objects.all(), required=False, label="Новый родитель"
    )


# Register your models here.
class ProductsGalleryInline(nested_admin.NestedTabularInline):
    model = ProductsGallery
    extra = 1


class ProductsCloudInline(nested_admin.NestedTabularInline):
    model = ProductsCloud
    extra = 0
    max_num = 1
    min_num = 1


class ProductsVariableInline(nested_admin.NestedTabularInline):
    model = ProductsVariable
    filter_horizontal = ["attribute"]
    extra = 1


@admin.display(boolean=True, description="Деф. изображение?")
def is_default_image(self, obj):
    return obj.image.name == "default/product-nophoto.png"


# Форма для массового обновления
class BulkUpdateForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    manufacturers = forms.ModelMultipleChoiceField(
        queryset=Manufacturers.objects.all(),
        widget=FilteredSelectMultiple("Производители", is_stacked=False),
        required=False,
        label="Заменить производителей на:"
    )
    site = forms.ModelMultipleChoiceField(
        queryset=Site.objects.all(),
        widget=FilteredSelectMultiple("Сайты", is_stacked=False),
        required=False,
        label="Заменить сайты на:"
    )


@admin.register(Products)
class ProductsAdmin(nested_admin.NestedModelAdmin):
    list_display = ["id", "name", "slug", "type", "price"]
    list_display_links = ["id", "name", "slug"]
    search_fields = ["name"]
    list_filter = ["category", "manufacturers", "site", ImageStatusFilter]
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ["atribute"]
    inlines = [ProductsCloudInline, ProductsVariableInline, ProductsGalleryInline]
    save_as = True
    save_on_top = True
    actions = ['mass_update_manufacturers_and_sites']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'mass-update-manufacturers-and-sites/',
                self.admin_site.admin_view(self.mass_update_view),
                name='mass_update_manufacturers_and_sites',
            ),
        ]
        return custom_urls + urls

    def mass_update_manufacturers_and_sites(self, request, queryset):
        selected = request.POST.getlist(ACTION_CHECKBOX_NAME)
        return redirect(f'mass-update-manufacturers-and-sites/?ids={",".join(selected)}')

    def mass_update_view(self, request):
        ids = request.GET.get("ids", "")
        selected_ids = ids.split(",") if ids else []

        if request.method == "POST":
            form = BulkUpdateForm(request.POST)
            if form.is_valid():
                manufacturers = form.cleaned_data["manufacturers"]
                sites = form.cleaned_data["site"]
                products = Products.objects.filter(id__in=selected_ids)

                for product in products:
                    if manufacturers:
                        product.manufacturers.set(manufacturers)
                    if sites:
                        product.site.set(sites)

                self.message_user(request, f"Обновлено {products.count()} товаров.")
                return redirect("..")
        else:
            form = BulkUpdateForm(initial={"_selected_action": selected_ids})

        return render(request, "admin/mass_update_manufacturers.html", {
            "form": form,
            "title": "Массовое обновление производителей и сайтов",
            "selected_ids": ",".join(selected_ids),
        })


@admin.register(ProductsVariable)
class ProductsVariableAdmin(admin.ModelAdmin):
    filter_horizontal = ["attribute"]


@admin.register(Valute)
class ValuteAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
    ]
    list_display_links = [
        "id",
        "name",
    ]
    search_fields = ["name"]


@admin.register(Manufacturers)
class ManufacturersAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "description"]
    prepopulated_fields = {
        "slug": ("name",),
    }
    list_display_links = ["id", "name", "description"]
    save_as = True
    save_on_top = True


class AtributeInline(admin.TabularInline):
    model = Atribute
    extra = 1


@admin.register(Variable)
class VariableAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    list_display_links = ["id", "name"]
    inlines = [AtributeInline]
    save_as = True
    save_on_top = True


@admin.register(Categories)
class CategoriesAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "slug", "description", "parent_slug"]
    search_fields = ["name"]
    filter_horizontal = ["products_rekomendet"]
    prepopulated_fields = {"slug": ("name",)}
    list_display_links = ["id", "name", "slug", "description"]
    save_as = True
    save_on_top = True
    list_filter = ["site"]
    actions = ["change_parent_action"]

    @admin.display(description="Родитель (slug)")
    def parent_slug(self, obj):
        return obj.parent.slug if obj.parent else "-"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "change-parent/",
                self.admin_site.admin_view(self.change_parent),
                name="shop_categories_change_parent",
            )
        ]
        return custom_urls + urls

    def change_parent_action(self, request, queryset):
        selected = request.POST.getlist(ACTION_CHECKBOX_NAME)
        return redirect(f'change-parent/?_selected_action={",".join(selected)}')

    change_parent_action.short_description = "Массово изменить родительскую категорию"

    def change_parent(self, request):
        ids = request.GET.get("_selected_action", "")
        selected_ids = ids.split(",")
        queryset = Categories.objects.filter(pk__in=selected_ids)

        if request.method == "POST":
            form = ChangeParentForm(request.POST)
            if form.is_valid():
                new_parent = form.cleaned_data["parent"]
                for category in queryset:
                    category.parent = new_parent
                    category.save()
                self.message_user(
                    request, f"Успешно изменен parent у {queryset.count()} категорий."
                )
                return redirect("..")
        else:
            form = ChangeParentForm(initial={"_selected_action": ids})

        context = {
            "title": "Массовое изменение родителя",
            "objects": queryset,
            "form": form,
            "opts": self.model._meta,
        }
        return TemplateResponse(request, "admin/change_parent.html", context)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["id", "amount", "user", "site"]
    list_display_links = ["id", "amount", "user", "site"]
    filter_horizontal = ["selectedproduct"]
    save_as = True
    save_on_top = True


@admin.register(Reviews)
class ReviewsAdmin(admin.ModelAdmin):
    list_display = [
        "text",
        "author",
        "product",
        "starvalue",
    ]
    list_display_links = [
        "text",
        "author",
        "product",
        "starvalue",
    ]
    save_as = True
    save_on_top = True


admin.site.register(ReviewImage)
admin.site.register(ImportHistory)
admin.site.register(StockAvailability)
admin.site.register(Storage)
admin.site.register(Complaint)
admin.site.register(SelectedProduct)
admin.site.register(Atribute)
admin.site.register(ProductsPrice)
admin.site.register(Tag)
admin.site.register(ReklamBanner)
admin.site.register(ProductsGallery)
admin.site.register(Brands)
admin.site.register(ProductExpense)
admin.site.register(ProductExpensePurchase)
admin.site.register(ProductExpensePosition)
admin.site.register(ManufacturersExpenseType)
admin.site.register(ManufacturersExpense)
admin.site.register(FaqsProducts)
admin.site.register(ManufacturersIncome)

from django.contrib import admin
from .models import *
from django_ace import AceWidget
from django import forms


class GeneralSettingsForm(forms.ModelForm):
    message_header = forms.CharField(
        widget=AceWidget(
            mode="html",
            readonly=False,
            behaviours=True,
            showgutter=True,
            wordwrap=False,
            usesofttabs=True,
        )
    )
    message_footer = forms.CharField(
        widget=AceWidget(
            mode="html",
            readonly=False,
            behaviours=True,
            showgutter=True,
            wordwrap=False,
            usesofttabs=True,
        )
    )


@admin.register(HomePage)
class HomePageAdmin(admin.ModelAdmin):
    model = HomePage


@admin.register(ExtendedSite)
class ExtendedSiteAdmin(admin.ModelAdmin):
    model = ExtendedSite


@admin.register(Comments)
class CommentsAdmin(admin.ModelAdmin):
    model = Comments


@admin.register(ContactPage)
class ContactPageAdmin(admin.ModelAdmin):
    model = ContactPage


@admin.register(ContactPageInformation)
class ContactPageInformationAdmin(admin.ModelAdmin):
    model = ContactPageInformation


@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
    model = AboutPage


@admin.register(Seo)
class SeoAdmin(admin.ModelAdmin):
    model = Seo


@admin.register(SettingsGlobale)
class SettingsGlobaleAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    list_display_links = ["id", "name"]


@admin.register(CategorysBlogs)
class CategorysBlogsAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "description"]
    prepopulated_fields = {
        "slug": ("name",),
    }
    list_display_links = ["id", "name", "description"]
    save_as = True
    save_on_top = True


@admin.register(TagsBlogs)
class TagsBlogsAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "description"]
    prepopulated_fields = {
        "slug": ("name",),
    }
    list_display_links = ["id", "name", "description"]
    save_as = True
    save_on_top = True


@admin.register(Blogs)
class BlogsAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "slug"]
    prepopulated_fields = {
        "slug": ("name",),
    }
    list_filter = ["site"]

    list_display_links = ["id", "name", "slug"]
    save_as = True
    save_on_top = True


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "slug"]
    prepopulated_fields = {
        "slug": ("name",),
    }
    list_display_links = ["id", "name", "slug"]
    save_as = True
    save_on_top = True


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "slug"]
    prepopulated_fields = {
        "slug": ("name",),
    }
    list_display_links = ["id", "name", "slug"]
    save_as = True
    save_on_top = True


@admin.register(GalleryMedia)
class GalleryMediaAdmin(admin.ModelAdmin):
    model = GalleryMedia


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "slug"]
    prepopulated_fields = {
        "slug": ("name",),
    }
    list_display_links = ["id", "name", "slug"]
    save_as = True
    save_on_top = True


@admin.register(ServiceMedia)
class ServiceMediaAdmin(admin.ModelAdmin):
    model = ServiceMedia


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "slug"]
    prepopulated_fields = {
        "slug": ("name",),
    }
    list_display_links = ["id", "name", "slug"]
    save_as = True
    save_on_top = True


@admin.register(PriceInfo)
class PriceInfoAdmin(admin.ModelAdmin):
    model = PriceInfo


@admin.register(Pages)
class PagesAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "description"]
    prepopulated_fields = {
        "slug": ("name",),
    }
    list_filter = ["site"]
    list_display_links = ["id", "name", "description"]
    save_as = True
    save_on_top = True


@admin.register(Faqs)
class FaqsAdmin(admin.ModelAdmin):
    list_display = ["id", "question"]
    list_display_links = ["id", "question"]
    save_as = True
    save_on_top = True

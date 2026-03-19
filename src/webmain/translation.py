from modeltranslation.translator import register, TranslationOptions
from .models import (
    Seo,
    SettingsGlobale,
    ContactPage,
    ContactPageInformation,
    AboutPage,
    HomePage,
    Pages,
    Faqs,
    CategorysBlogs,
    TagsBlogs,
    Blogs,
    Sponsorship,
    Gallery,
    Service,
    Price,
    PriceInfo,
)


@register(Seo)
class SeoTranslationOptions(TranslationOptions):
    fields = ("title", "metadescription", "propertytitle", "propertydescription")


@register(SettingsGlobale)
class SettingsGlobaleTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "content",
        "description",
        "slogan",
        "message_header",
        "message_footer",
    )


@register(ContactPage)
class ContactPageTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "metadescription",
        "propertytitle",
        "propertydescription",
        "jsontemplate",
    )


@register(ContactPageInformation)
class ContactPageInformationTranslationOptions(TranslationOptions):
    fields = ("title_contact", "description_contact", "information_contact")


@register(AboutPage)
class AboutPageTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "metadescription",
        "propertytitle",
        "propertydescription",
        "jsontemplate",
    )


@register(HomePage)
class HomePageTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "metadescription",
        "propertytitle",
        "propertydescription",
        "jsontemplate",
    )


@register(Pages)
class PagesTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
        "title",
        "metadescription",
        "propertytitle",
        "propertydescription",
    )


@register(Faqs)
class FaqsTranslationOptions(TranslationOptions):
    fields = ("question", "answer")


@register(CategorysBlogs)
class CategorysBlogsTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
        "title",
        "metadescription",
        "propertytitle",
        "propertydescription",
    )


@register(TagsBlogs)
class TagsBlogsTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
        "title",
        "metadescription",
        "propertytitle",
        "propertydescription",
    )


@register(Blogs)
class BlogsTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
        "resource",
        "title",
        "metadescription",
        "propertytitle",
        "propertydescription",
    )


@register(Sponsorship)
class SponsorshipTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
        "resource",
        "title",
        "metadescription",
        "propertytitle",
        "propertydescription",
    )


@register(Gallery)
class GalleryTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
        "title",
        "metadescription",
        "propertytitle",
        "propertydescription",
    )


@register(Service)
class ServiceTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
        "title",
        "metadescription",
        "propertytitle",
        "propertydescription",
    )


@register(Price)
class PriceTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
        "title",
        "metadescription",
        "propertytitle",
        "propertydescription",
    )


@register(PriceInfo)
class PriceInfoTranslationOptions(TranslationOptions):
    fields = ("name", "description", "amount", "meaning")

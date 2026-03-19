from modeltranslation.translator import register, TranslationOptions
from .models import (
    Manufacturers,
    Categories,
    Variable,
    Atribute,
    Products,
    ProductsVariable,
    ApplicationsProducts,
    Valute,
    FaqsProducts,
    Reviews,
    Complaint,
    ProductComment,
    Storage,
)


@register(Manufacturers)
class ManufacturersTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
        "title",
        "metadescription",
        "propertytitle",
        "propertydescription",
        "company_name",
        "company_inn",
        "company_director",
        "company_adress",
    )


@register(Categories)
class CategoriesTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
        "title",
        "metadescription",
        "propertytitle",
        "propertydescription",
    )


@register(Variable)
class VariableTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Atribute)
class AtributeTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "content",
    )


@register(Products)
class ProductsTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "fragment",
        "description",
        "title",
        "metadescription",
        "propertytitle",
        "propertydescription",
    )


@register(ProductsVariable)
class ProductsVariableTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "title",
        "metadescription",
        "propertytitle",
        "propertydescription",
    )


@register(ApplicationsProducts)
class ApplicationsProductsTranslationOptions(TranslationOptions):
    fields = ("content",)


@register(Valute)
class ValuteTranslationOptions(TranslationOptions):
    fields = (
        "name",
    )


@register(FaqsProducts)
class FaqsProductsTranslationOptions(TranslationOptions):
    fields = (
        "question",
        "answer",
    )


@register(Reviews)
class ReviewsTranslationOptions(TranslationOptions):
    fields = ("text",)


@register(Complaint)
class ComplaintTranslationOptions(TranslationOptions):
    fields = ("description",)


@register(ProductComment)
class ProductCommentTranslationOptions(TranslationOptions):
    fields = ("content",)


@register(Storage)
class StorageTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "address",
        "city",
        "content",
        "email",
        "delivery_comment",
    )

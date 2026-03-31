import json

from django import forms
from django.contrib.sites.models import Site
from django.forms import Textarea
from slugify import slugify
from django.core.validators import FileExtensionValidator
from multiupload.fields import MultiFileField
from django_ace import AceWidget
from django.contrib.auth import get_user_model
from django.forms.widgets import CheckboxSelectMultiple

from documentation.models import Documentations
from payment.models import PaymentType
from .models import (
    TicketComment,
    Asset,
    Notificationgroups,
    Ticket,
    Groups,
    Collaborations, EmailTemplate, CallRecord, CallSettings, VoiceMenu, CallQueue, PhoneNumber, IntegrationService,
    AdditionalService, MessengerIntegration, DeliveryIntegration, PaymentIntegration, LoyaltyLevel, LoyaltySettings,
    LoyaltyPromoCode, LoyaltyProgram,
)
from _project.settings import LANGUAGES

from webmain.models import (
    ExtendedSite,
    Price,
    Gallery,
    Service,
    SettingsGlobale,
    HomePage,
    AboutPage,
    ContactPage,
    Faqs,
    Blogs,
    CategorysBlogs,
    TagsBlogs,
    Pages,
    Seo,
    ContactPageInformation,
    Sponsorship,
)
from modeltranslation.utils import get_translation_fields

from useraccount.models import Withdrawal, Profile
from unidecode import unidecode
from django.db import transaction, models
from hr.models import Schedule, Vacancy, LessonMaterial, Lesson
from shop.models import (
    Atribute,
    Complaint,
    Categories,ImportHistory,
    Products,
    Reviews,
    ProductExpensePosition,
    ProductExpensePurchase,
    Variable,
    ProductsVariable,
)
from ckeditor.widgets import CKEditorWidget
from crm.models import StatusPayment
from payment.models import Order
from development.models import  SettingsModeration
from shop.models import SelectedProduct

from shop.models import ProductExpense


class TicketCommentForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(
            attrs={"placeholder": "Написать комментарий", "class": "form-control"}
        )
    )
    files = MultiFileField(
        required=False,
        max_num=10,
        attrs={"class": "form-control cursor-pointer form-file"},
    )

    class Meta:
        model = TicketComment
        fields = ["content", "files"]

    def clean_files(self):
        files = self.cleaned_data.get("files")
        if files:
            for file in files:
                try:
                    FileExtensionValidator(
                        allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
                    )(file)
                except forms.ValidationError:
                    self.add_error(
                        "files", f"Файл '{file.name}' имеет недопустимое расширение."
                    )
        return files


class SettingsGlobaleForm(forms.ModelForm):
    logo = forms.ImageField(
        required=False,
        widget=forms.FileInput(
            attrs={"class": "form-file-input form-control", "id": "general_logo"}
        ),
    )
    logo_lg = forms.ImageField(
        required=False,
        widget=forms.FileInput(
            attrs={"class": "form-file-input form-control", "id": "logo_lg"}
        ),
    )
    logo_sm = forms.ImageField(
        required=False,
        widget=forms.FileInput(
            attrs={"class": "form-file-input form-control", "id": "logo_sm"}
        ),
    )
    logo_white = forms.ImageField(
        required=False,
        widget=forms.FileInput(
            attrs={"class": "form-file-input form-control", "id": "logo_white"}
        ),
    )
    logo_white_lg = forms.ImageField(
        required=False,
        widget=forms.FileInput(
            attrs={"class": "form-file-input form-control", "id": "logo_white_lg"}
        ),
    )
    logo_white_sm = forms.ImageField(
        required=False,
        widget=forms.FileInput(
            attrs={"class": "form-file-input form-control", "id": "logo_white_sm"}
        ),
    )
    favicon = forms.ImageField(
        required=False,
        widget=forms.FileInput(
            attrs={"class": "form-file-input form-control", "id": "favicon"}
        ),
    )
    paymentmethod = forms.ImageField(
        required=False,
        widget=forms.FileInput(
            attrs={"class": "form-file-input form-control", "id": "paymentmethod"}
        ),
    )
    name = forms.CharField(
        required=True,
        max_length=256,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Название",
                "id": "global_name",
                "class": "form-control input-default ",
            }
        ),
    )
    content = forms.CharField(
        max_length=256,
        required=False,
        widget=forms.Textarea(
            attrs={"placeholder": "Копирайт", "class": "form-control input-default "}
        ),
    )
    description = forms.CharField(
        max_length=256,
        required=False,
        widget=forms.Textarea(
            attrs={"placeholder": "Описание", "class": "form-control input-default "}
        ),
    )
    message_header = forms.CharField(
        widget=AceWidget(
            mode="html",
            width="100%",
            height="500px",
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
            width="100%",
            height="500px",
            readonly=False,
            behaviours=True,
            showgutter=True,
            wordwrap=False,
            usesofttabs=True,
        )
    )
    yandex_metrica = forms.CharField(
        max_length=1024,
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": "Яндекс Метрика",
                "class": "form-control input-default ",
            }
        ),
    )
    google_analitic = forms.CharField(
        max_length=1024,
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": "Google Аналитика",
                "class": "form-control input-default ",
            }
        ),
    )
    email_host = forms.CharField(
        max_length=256,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Email Site HOST",
                "class": "form-control input-default ",
            }
        ),
    )
    default_from_email = forms.CharField(
        max_length=256,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Email Site From",
                "class": "form-control input-default ",
            }
        ),
    )
    email_port = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Email Site PORT",
                "class": "form-control input-default ",
            }
        ),
    )
    email_host_user = forms.CharField(
        max_length=256,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Email Site User",
                "class": "form-control input-default ",
            }
        ),
    )
    email_host_password = forms.CharField(
        max_length=256,
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Email Site Password",
                "class": "form-control input-default ",
            }
        ),
    )
    email_use_tls = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        initial=False,
    )
    email_use_ssl = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        initial=False,
    )
    json_data = forms.CharField(
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": "JSON данные"}
        ),
        required=False,
    )

    class Meta:
        model = SettingsGlobale
        fields = [
            "logo",
            "logo_lg",
            "logo_sm",
            "logo_white",
            "logo_white_lg",
            "logo_white_sm",
            "favicon",
            "paymentmethod",
            "name",
            "description",
            "content",
            "message_header",
            "message_footer",
            "yandex_metrica",
            "google_analitic",
            "email_host",
            "default_from_email",
            "email_port",
            "email_host_user",
            "email_host_password",
            "email_use_tls",
            "email_use_ssl",
            "jsontemplate",
        ]

    def __init__(self, *args, **kwargs):
        super(SettingsGlobaleForm, self).__init__(*args, **kwargs)


class HomepageSetForm(forms.ModelForm):
    # Первый блок
    previev = forms.FileField(
        required=False,
        widget=forms.FileInput(
            attrs={"class": "form-file-input form-control", "id": "previev"}
        ),
    )
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Мета-заголовок",
                "class": "form-control input-default",
            }
        ),
    )
    metadescription = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": "Мета-описание",
                "class": "form-control input-default",
            }
        ),
    )
    propertytitle = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Мета-заголовок для previev",
                "class": "form-control input-default",
            }
        ),
    )
    propertydescription = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": "Мета-описание для previev",
                "class": "form-control input-default",
            }
        ),
    )
    text = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": "Мета-описание для previev",
                "class": "form-control input-default",
            }
        ),
    )
    json_data = forms.CharField(
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": "JSON данные"}
        ),
        required=False,
    )

    # Добавляем поле для загрузки нового json файла

    class Meta:
        model = HomePage
        fields = [
            "previev",
            "title",
            "metadescription",
            "propertytitle",
            "propertydescription",
            "text",
            "jsontemplate",
        ]

    def __init__(self, *args, **kwargs):
        super(HomepageSetForm, self).__init__(*args, **kwargs)


class CollaborationsForm(forms.ModelForm):
    class Meta:
        model = Collaborations
        fields = [
            "name",
            "email",
            "subject",
            "phone",
            "message",
        ]  # Перечень полей, которые будут в форме
        widgets = {
            "message": forms.Textarea(
                attrs={"rows": 4, "cols": 40}
            ),  # Пример кастомизации поля 'message'
        }

    # Добавляем кастомные валидации, если нужно
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if "@" not in email:
            raise forms.ValidationError("Введите правильный адрес электронной почты.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if len(phone) < 10:  # Пример валидации для номера телефона
            raise forms.ValidationError(
                "Номер телефона должен содержать минимум 10 цифр."
            )
        return phone


class AboutPageForm(forms.ModelForm):
    previev = forms.FileField(
        required=False,
        widget=forms.FileInput(
            attrs={"class": "form-file-input form-control", "id": "previev"}
        ),
    )
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Мета-заголовок <страницы о проекте>",
                "class": "form-control input-default",
            }
        ),
    )
    metadescription = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": "Мета-описание <страницы о проекте>",
                "class": "form-control input-default",
            }
        ),
    )
    propertytitle = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Мета-заголовок для previev <страницы о проекте>",
                "class": "form-control input-default",
            }
        ),
    )
    propertydescription = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": "Мета-описание для previev <страницы о проекте>",
                "class": "form-control input-default",
            }
        ),
    )
    text = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": "Мета-описание для previev <страницы о проекте>",
                "class": "form-control input-default",
            }
        ),
    )
    json_data = forms.CharField(
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": "JSON данные"}
        ),
        required=False,
    )

    class Meta:
        model = AboutPage
        fields = "__all__"


class FaqsForm(forms.ModelForm):
    site = forms.ModelMultipleChoiceField(
        queryset=Site.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",
                "id": "choices-multiple-site",
                "data-choices": "",
                "name": "choices-multiple-default",
                "multiple": "multiple",
            }
        ),
        required=False,
    )

    class Meta:
        model = Faqs
        fields = ["question", "site", "answer"]
        widgets = {
            "question": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Введите вопрос",
                }
            ),
            "answer": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Введите ответ",
                }
            ),
        }


class BlogsForm(forms.ModelForm):
    category = forms.ModelMultipleChoiceField(
        queryset=CategorysBlogs.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",
                "id": "choices-multiple-default",
                "data-choices": "",
                "name": "choices-multiple-default",
                "multiple": "multiple",
            }
        ),
        required=False,
    )
    site = forms.ModelMultipleChoiceField(
        queryset=Site.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",
                "id": "choices-multiple-site",
                "data-choices": "",
                "name": "choices-multiple-default",
                "multiple": "multiple",
            }
        ),
        required=False,
    )

    tags = forms.ModelMultipleChoiceField(
        queryset=TagsBlogs.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",
                "id": "choices-multiple-tags",
                "data-choices": "",
                "name": "choices-multiple-tags",
                "multiple": "multiple",
            }
        ),
        required=False,
    )

    publishet = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Черновик",
    )

    class Meta:
        model = Blogs
        fields = [
            "name",
            "description",
            "title",
            "metadescription",
            "author",
            "resource",
            "category",
            "slug",
            "propertytitle",
            "propertydescription",
            "previev",
            "cover",
            "site",
            "publishet",
        ]
        widgets = {
            "author": forms.Select(
                attrs={
                    "class": "default-select form-control wide",
                    "placeholder": "Автор",
                }
            ),
            "name": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Название"}
            ),
            "resource": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Источник"}
            ),
            "description": forms.Textarea(),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Заголовок",
                }
            ),
            "metadescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Содержимое",
                }
            ),
            "category": forms.SelectMultiple(
                attrs={
                    "class": "default-select form-control wide",
                    "id": "id_category",
                    "aria-label": "Выберите категории",
                    "name": "category",
                }
            ),
            "site": forms.SelectMultiple(
                attrs={
                    "class": "default-select form-control wide",
                    "id": "id_site",
                    "aria-label": "Выберите сайты",
                    "name": "site",
                }
            ),
            "slug": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Slug"}
            ),
            "propertytitle": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Заголовок свойства",
                }
            ),
            "propertydescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Описание свойства",
                }
            ),
            "previev": forms.FileInput(attrs={"class": "form-file-input form-control"}),
            "cover": forms.FileInput(attrs={"class": "form-file-input form-control"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Генерация slug из name с помощью slugify
        instance.slug = slugify(instance.name)

        if commit:
            instance.save()
            self.cleaned_data["site"] and instance.site.set(
                self.cleaned_data["site"]
            )  # Устанавливаем ManyToMany связь
        else:
            self.save_m2m = lambda: instance.site.set(
                self.cleaned_data["site"]
            )  # Для случая commit=False

        return instance


class StatusPaymentForm(forms.ModelForm):
    class Meta:
        model = StatusPayment
        fields = ["amount", "description", "status"]


class VacancyForm(forms.ModelForm):
    site = forms.ModelMultipleChoiceField(
        queryset=Site.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",
                "id": "choices-multiple-site",
                "data-choices": "",
                "name": "choices-multiple-site",
                "multiple": "multiple",
            }
        ),
        required=False,
    )

    work_schedule = forms.ChoiceField(
        choices=Vacancy.WORK_SCHEDULE_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "default-select form-control wide",
                "placeholder": "Выберите график работы",
            }
        ),
    )

    class Meta:
        model = Vacancy
        fields = [
            "title",
            "description",
            "requirements",
            "salary",
            "location",
            "work_schedule",
            "image",
            "site",
            "slug",
            "is_active",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Название вакансии",
                }
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control input-default", "placeholder": "Описание"}
            ),
            "requirements": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Требования",
                }
            ),
            "salary": forms.NumberInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Заработная плата",
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Город, адрес",
                }
            ),
            "slug": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Slug"}
            ),
            "image": forms.FileInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.title)

        if commit:
            instance.save()
            if self.cleaned_data.get("site"):
                instance.site.set(self.cleaned_data["site"])
        else:
            self.save_m2m = lambda: instance.site.set(self.cleaned_data["site"])

        return instance


class GalleryForm(forms.ModelForm):
    site = forms.ModelMultipleChoiceField(
        queryset=Site.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",
                "id": "choices-multiple-site",
                "data-choices": "",
                "name": "choices-multiple-default",
                "multiple": "multiple",
            }
        ),
        required=False,
    )

    publishet = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Черновик",
    )
    files = MultiFileField(
        required=False,
        max_num=10,
        attrs={"class": "form-control cursor-pointer form-file"},
    )

    class Meta:
        model = Gallery

        fields = [
            "name",
            "description",
            "title",
            "metadescription",
            "author",
            "slug",
            "propertytitle",
            "propertydescription",
            "previev",
            "cover",
            "image",
            "site",
            "publishet",
            "files",
        ]

        widgets = {
            "author": forms.Select(
                attrs={
                    "class": "default-select form-control wide",
                    "placeholder": "Автор",
                }
            ),
            "name": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Название"}
            ),
            "description": forms.Textarea(),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Заголовок",
                }
            ),
            "metadescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Содержимое",
                }
            ),
            "site": forms.SelectMultiple(
                attrs={
                    "class": "default-select form-control wide",
                    "id": "id_site",
                    "aria-label": "Выберите сайты",
                    "name": "site",
                }
            ),
            "slug": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Slug"}
            ),
            "propertytitle": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Заголовок свойства",
                }
            ),
            "propertydescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Описание свойства",
                }
            ),
            "previev": forms.FileInput(
                attrs={"class": "form-file-input form-control", "id": "id_previev"}
            ),
            "cover": forms.FileInput(
                attrs={"class": "form-file-input form-control", "id": "id_cover"}
            ),
            "image": forms.FileInput(attrs={"class": "form-file-input form-control"}),
        }

    def clean_files(self):
        files = self.cleaned_data.get("files")
        if files:
            for file in files:
                try:
                    FileExtensionValidator(
                        allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
                    )(file)
                except forms.ValidationError:
                    self.add_error(
                        "files", f"Файл '{file.name}' имеет недопустимое расширение."
                    )
        return files

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Генерация slug из name с помощью slugify
        instance.slug = slugify(instance.name)

        if commit:
            instance.save()
            self.cleaned_data["site"] and instance.site.set(
                self.cleaned_data["site"]
            )  # Устанавливаем ManyToMany связь
        else:
            self.save_m2m = lambda: instance.site.set(
                self.cleaned_data["site"]
            )  # Для случая commit=False

        return instance


class PriceForm(forms.ModelForm):
    site = forms.ModelMultipleChoiceField(
        queryset=Site.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",
                "id": "choices-multiple-site",
                "data-choices": "",
                "name": "choices-multiple-default",
                "multiple": "multiple",
            }
        ),
        required=False,
    )

    publishet = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Черновик",
    )

    class Meta:
        model = Price

        fields = [
            "name",
            "description",
            "title",
            "metadescription",
            "author",
            "slug",
            "propertytitle",
            "propertydescription",
            "site",
            "publishet",
        ]

        widgets = {
            "author": forms.Select(
                attrs={
                    "class": "default-select form-control wide",
                    "placeholder": "Автор",
                }
            ),
            "name": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Название"}
            ),
            "description": forms.Textarea(),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Заголовок",
                }
            ),
            "metadescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Содержимое",
                }
            ),
            "site": forms.SelectMultiple(
                attrs={
                    "class": "default-select form-control wide",
                    "id": "id_site",
                    "aria-label": "Выберите сайты",
                    "name": "site",
                }
            ),
            "slug": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Slug"}
            ),
            "propertytitle": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Заголовок свойства",
                }
            ),
            "propertydescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Описание свойства",
                }
            ),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Генерация slug из name с помощью slugify
        instance.slug = slugify(instance.name)

        if commit:
            instance.save()
            self.cleaned_data["site"] and instance.site.set(
                self.cleaned_data["site"]
            )  # Устанавливаем ManyToMany связь
        else:
            self.save_m2m = lambda: instance.site.set(
                self.cleaned_data["site"]
            )  # Для случая commit=False

        return instance


class ServiceForm(forms.ModelForm):
    site = forms.ModelMultipleChoiceField(
        queryset=Site.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",
                "id": "choices-multiple-site",
                "data-choices": "",
                "name": "choices-multiple-default",
                "multiple": "multiple",
            }
        ),
        required=False,
    )

    publishet = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Черновик",
    )
    files = MultiFileField(
        required=False,
        max_num=10,
        attrs={"class": "form-control cursor-pointer form-file"},
    )

    class Meta:
        model = Service

        fields = [
            "name",
            "description",
            "title",
            "metadescription",
            "author",
            "slug",
            "propertytitle",
            "propertydescription",
            "previev",
            "cover",
            "image",
            "site",
            "publishet",
            "files",
        ]

        widgets = {
            "author": forms.Select(
                attrs={
                    "class": "default-select form-control wide",
                    "placeholder": "Автор",
                }
            ),
            "name": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Название"}
            ),
            "description": CKEditorWidget(),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Заголовок",
                }
            ),
            "metadescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Содержимое",
                }
            ),
            "site": forms.SelectMultiple(
                attrs={
                    "class": "default-select form-control wide",
                    "id": "id_site",
                    "aria-label": "Выберите сайты",
                    "name": "site",
                }
            ),
            "slug": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Slug"}
            ),
            "propertytitle": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Заголовок свойства",
                }
            ),
            "propertydescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Описание свойства",
                }
            ),
            "previev": forms.FileInput(attrs={"class": "form-file-input form-control"}),
            "cover": forms.FileInput(attrs={"class": "form-file-input form-control"}),
            "image": forms.FileInput(attrs={"class": "form-file-input form-control"}),
        }

    def clean_files(self):
        files = self.cleaned_data.get("files")
        if files:
            for file in files:
                try:
                    FileExtensionValidator(
                        allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
                    )(file)
                except forms.ValidationError:
                    self.add_error(
                        "files", f"Файл '{file.name}' имеет недопустимое расширение."
                    )
        return files

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Генерация slug из name с помощью slugify
        instance.slug = slugify(instance.name)

        if commit:
            instance.save()
            self.cleaned_data["site"] and instance.site.set(
                self.cleaned_data["site"]
            )  # Устанавливаем ManyToMany связь
        else:
            self.save_m2m = lambda: instance.site.set(
                self.cleaned_data["site"]
            )  # Для случая commit=False

        return instance


class SponsorshipForm(forms.ModelForm):
    blogs = forms.ModelMultipleChoiceField(
        queryset=Blogs.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",
                "id": "choices-multiple-tags",
                "data-choices": "",
                "name": "choices-multiple-tags",
                "multiple": "multiple",
            }
        ),
        required=False,
    )
    site = forms.ModelMultipleChoiceField(
        queryset=Site.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",
                "id": "choices-multiple-site",
                "data-choices": "",
                "name": "choices-multiple-default",
                "multiple": "multiple",
            }
        ),
        required=False,
    )

    class Meta:
        model = Sponsorship
        fields = [
            "author",
            "resource",
            "blogs",
            "name",
            "description",
            "previev",
            "title",
            "metadescription",
            "propertytitle",
            "propertydescription",
            "cover",
            "image",
            "publishet",
            "site",
        ]
        widgets = {
            "author": forms.Select(attrs={"class": "form-control"}),
            "resource": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Источник"}
            ),
            "blogs": forms.SelectMultiple(attrs={"class": "form-control"}),
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Описание"}
            ),
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Мета-заголовок"}
            ),
            "metadescription": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Мета-описание"}
            ),
            "propertytitle": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Мета-заголовок ссылки"}
            ),
            "propertydescription": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Мета-описание ссылки"}
            ),
            "publishet": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "site": forms.SelectMultiple(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Генерация slug из name с помощью slugify
        instance.slug = slugify(instance.name)

        if commit:
            instance.save()
            self.cleaned_data["site"] and instance.site.set(
                self.cleaned_data["site"]
            )  # Устанавливаем ManyToMany связь
        else:
            self.save_m2m = lambda: instance.site.set(
                self.cleaned_data["site"]
            )  # Для случая commit=False

        return instance


class PagesForm(forms.ModelForm):
    site = forms.ModelMultipleChoiceField(
        queryset=Site.objects.all(),
        widget=forms.SelectMultiple(
            attrs={  # <-- Используем SelectMultiple
                "class": "form-control",
                "id": "choices-multiple-site",  # Используйте тот же ID, как в GalleryForm
                "data-choices": "",
                "name": "choices-multiple-default",
                "multiple": "multiple",
            }
        ),
        required=False,
    )

    class Meta:
        model = Pages
        fields = [
            "pagetype",
            "name",
            "description",
            "title",
            "site",
            "metadescription",
            "slug",
            "propertytitle",
            "propertydescription",
            "previev",
            "site",
            "publishet",
        ]
        widgets = {
            "pagetype": forms.Select(
                attrs={
                    "class": "default-select form-control wide",
                    "placeholder": "Тип страницы",
                }
            ),
            "name": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Название"}
            ),
            "description": forms.Textarea(),
            "slug": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Slug"}
            ),
            "previev": forms.FileInput(attrs={"class": "form-file-input form-control"}),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Заголовок",
                }
            ),
            "metadescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Мета-описание",
                }
            ),
            "propertytitle": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Мета-заголовок ссылки",
                }
            ),
            "propertydescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Мета-описание ссылки",
                }
            ),
            "site": forms.SelectMultiple(
                attrs={  # <-- В Meta.widgets тоже SelectMultiple
                    "class": "default-select form-control wide",
                    "id": "id_site",
                    "aria-label": "Выберите сайты",
                    "name": "site",
                }
            ),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Генерация slug из name с помощью slugify
        instance.slug = slugify(instance.name)

        if commit:
            instance.save()
            self.cleaned_data["site"] and instance.site.set(
                self.cleaned_data["site"]
            )  # Устанавливаем ManyToMany связь
        else:
            self.save_m2m = lambda: instance.site.set(
                self.cleaned_data["site"]
            )  # Для случая commit=False

        return instance


class SeoForm(forms.ModelForm):
    class Meta:
        model = Seo
        fields = [
            "pagetype",
            "previev",
            "metadescription",
            "title",
            "propertytitle",
            "propertydescription",
            "site",
        ]
        widgets = {
            "pagetype": forms.Select(
                attrs={
                    "class": "default-select form-control wide",
                    "placeholder": "Тип страницы",
                }
            ),
            "previev": forms.FileInput(attrs={"class": "form-file-input form-control"}),
            "site": forms.Select(
                attrs={
                    "class": "default-select form-control wide",
                    "placeholder": "Сайт",
                }
            ),
            "metadescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Мета-описание",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Мета-заголовок",
                }
            ),
            "propertytitle": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Мета-заголовок ссылки",
                }
            ),
            "propertydescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Мета-описание ссылки",
                }
            ),
        }


class NotificationForm(forms.ModelForm):
    user = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "default-select form-control wide",
                "id": "id_user",
                "aria-label": "Выберите пользователей",
            }
        ),
    )

    class Meta:
        model = Notificationgroups
        fields = ["content_type", "user", "message", "object_id"]
        widgets = {
            "content_type": forms.Select(
                attrs={
                    "class": "default-select form-control wide",
                    "placeholder": "Тип контента",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Сообщение",
                }
            ),
            "object_id": forms.NumberInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "ID объекта",
                }
            ),
            "slug": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Slug"}
            ),
        }


class CategorysBlogsForm(forms.ModelForm):
    site = forms.ModelMultipleChoiceField(
        queryset=Site.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",
                "id": "choices-multiple-site",
                "data-choices": "",
                "name": "choices-multiple-default",
                "multiple": "multiple",
            }
        ),
        required=False,
    )

    class Meta:
        model = CategorysBlogs
        fields = [
            "name",
            "slug",
            "description",
            "parent",
            "cover",
            "icon",
            "image",
            "previev",
            "title",
            "metadescription",
            "publishet",
            "site",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Название"}
            ),
            "slug": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Slug"}
            ),
            "description": Textarea(
                attrs={"class": "form-control input-default", "placeholder": "Описание"}
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Заголовок",
                }
            ),
            "metadescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Мета-описание",
                }
            ),
            "propertytitle": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Заголовок",
                }
            ),
            "propertydescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Мета-описание",
                }
            ),
            "parent": forms.Select(
                attrs={
                    "class": "default-select form-control wide",
                    "placeholder": "Родитель",
                }
            ),
            "icon": forms.FileInput(attrs={"class": "form-file-input form-control"}),
            "image": forms.FileInput(attrs={"class": "form-file-input form-control"}),
            "cover": forms.FileInput(attrs={"class": "form-file-input form-control"}),
            "site": forms.SelectMultiple(
                attrs={
                    "class": "default-select form-control wide",
                    "id": "id_site",
                    "aria-label": "Выберите сайты",
                    "name": "site",
                }
            ),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Генерация slug из name с помощью slugify
        instance.slug = slugify(instance.name)

        if commit:
            instance.save()
            self.cleaned_data["site"] and instance.site.set(
                self.cleaned_data["site"]
            )  # Устанавливаем ManyToMany связь
        else:
            self.save_m2m = lambda: instance.site.set(
                self.cleaned_data["site"]
            )  # Для случая commit=False

        return instance


class TagsBlogsForm(forms.ModelForm):
    site = forms.ModelMultipleChoiceField(
        queryset=Site.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",
                "id": "choices-multiple-site",
                "data-choices": "",
                "name": "choices-multiple-default",
                "multiple": "multiple",
            }
        ),
        required=False,
    )

    class Meta:
        model = TagsBlogs
        fields = [
            "name",
            "slug",
            "description",
            "cover",
            "icon",
            "image",
            "previev",
            "title",
            "metadescription",
            "propertytitle",
            "propertydescription",
            "publishet",
            "site",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Название"}
            ),
            "slug": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Slug"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control input-default", "placeholder": "Описание"}
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Заголовок",
                }
            ),
            "metadescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Мета-описание",
                }
            ),
            "propertytitle": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Мета-заголовок ссылки",
                }
            ),
            "propertydescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Мета-описание ссылки",
                }
            ),
            "icon": forms.FileInput(attrs={"class": "form-file-input form-control"}),
            "image": forms.FileInput(attrs={"class": "form-file-input form-control"}),
            "cover": forms.FileInput(attrs={"class": "form-file-input form-control"}),
            "site": forms.SelectMultiple(
                attrs={
                    "class": "default-select form-control wide",
                    "id": "id_site",
                    "aria-label": "Выберите сайты",
                    "name": "site",
                }
            ),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            base_slug = slugify(instance.name)
            slug = base_slug
            counter = 1
            while TagsBlogs.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            instance.slug = slug
        if commit:
            instance.save()
        return instance


class WithdrawForm(forms.ModelForm):
    class Meta:
        model = Withdrawal
        fields = ["amount", "user"]
        widgets = {
            "amount": forms.NumberInput(
                attrs={"class": "form-control input-default", "placeholder": "Сумма"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")

        # Проверка на баланс пользователя
        if self.user:
            balance = float(self.user.balance)
            if amount > balance:
                # Используем форматирование для вывода ошибки без лишней точки
                raise forms.ValidationError(
                    f"Вы не можете списать больше {balance:.2f}."
                )

        return amount


class ContactPageInformationForm(forms.ModelForm):
    class Meta:
        model = ContactPageInformation
        fields = [
            "page_type",
            "image",
            "title_contact",
            "description_contact",
            "information_contact",
        ]


class ContactPageForm(forms.ModelForm):
    previev = forms.FileField(
        required=False,
        widget=forms.FileInput(
            attrs={"class": "form-file-input form-control", "id": "previev"}
        ),
    )
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Мета-заголовок <страницы о проекте>",
                "class": "form-control input-default",
            }
        ),
    )
    metadescription = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": "Мета-описание <страницы о проекте>",
                "class": "form-control input-default",
            }
        ),
    )
    propertytitle = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Мета-заголовок для previev <страницы о проекте>",
                "class": "form-control input-default",
            }
        ),
    )
    propertydescription = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": "Мета-описание для previev <страницы о проекте>",
                "class": "form-control input-default",
            }
        ),
    )
    json_data = forms.CharField(
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": "JSON данные"}
        ),
        required=False,
    )

    class Meta:
        model = ContactPage
        fields = "__all__"


class TicketWithCommentForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(
            attrs={"placeholder": "Написать комментарий", "class": "form-control "}
        )
    )
    files = MultiFileField(
        required=False,
        max_num=10,
        attrs={"class": "form-control cursor-pointer form-file"},
    )

    class Meta:
        model = Ticket
        fields = ["themas"]
        widgets = {
            "themas": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Тема"}
            ),
        }

    def clean_files(self):
        files = self.cleaned_data.get("files")
        if files:
            for file in files:
                try:
                    FileExtensionValidator(
                        allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
                    )(file)
                except forms.ValidationError:
                    self.add_error(
                        "files", f"Файл '{file.name}' имеет недопустимое расширение."
                    )
        return files


class PaymentTypeForm(forms.ModelForm):
    turn_on = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Включить",
    )

    class Meta:
        model = PaymentType
        fields = ["type", "content", "key_1", "key_2", "shop_key", "image", "turn_on"]
        widgets = {
            "type": forms.Select(
                attrs={
                    "class": "default-select form-control wide",
                    "placeholder": "Тип",
                }
            ),
            "content": forms.Textarea(
                attrs={"class": "form-control input-default", "placeholder": "Описание"}
            ),
            "key_1": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Первый ключ (public key)",
                }
            ),
            "key_2": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Второй ключ (secret key)",
                }
            ),
            "shop_key": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Ключ магазина (shop key)",
                }
            ),
            "image": forms.FileInput(attrs={"class": "form-file-input form-control"}),
        }


class DocumentationForm(forms.ModelForm):
    TYPE_CHOICES = [
        (0, "Сотрудник"),
        (1, "Обычный"),
        (2, "Юр лицо"),
        (3, "Компания"),
    ]
    type = forms.ChoiceField(
        choices=TYPE_CHOICES, widget=forms.Select(attrs={"class": "form-control"})
    )
    description = forms.CharField(
        widget=forms.Textarea(
            attrs={"placeholder": "Написать комментарий", "class": "form-control"}
        )
    )
    files = MultiFileField(
        required=False,
        max_num=10,
        attrs={"class": "form-control cursor-pointer form-file"},
    )
    name = forms.CharField(
        widget=forms.TextInput(
            attrs={"placeholder": "Название", "class": "form-control "}
        )
    )

    class Meta:
        model = Documentations
        fields = ["name", "description", "type", "files"]

    def clean_files(self):
        files = self.cleaned_data.get("files")
        if files:
            for file in files:
                try:
                    FileExtensionValidator(
                        allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
                    )(file)
                except forms.ValidationError:
                    self.add_error(
                        "files", f"Файл '{file.name}' имеет недопустимое расширение."
                    )
        return files


User = get_user_model()  # Модель пользователей, если вы используете кастомную


class GroupForm(forms.ModelForm):
    class Meta:
        model = Groups
        fields = ["name", "types", "users"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название"}
            ),
            "users": forms.SelectMultiple(
                attrs={
                    "class": "default-select form-control wide",
                    "id": "footer_blogs",
                    "aria-label": "Выберите пользователя",
                    "data-choices": "true",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор пользователей только теми, у кого type=0 (Сотрудник)
        self.fields["users"].queryset = Profile.objects.filter(type=0)


class WorkerUpdateProfileForm(forms.ModelForm):
    GENDER_CHOICES = [(1, "Мужской"), (2, "Женский")]

    avatar = forms.ImageField(
        required=False, widget=forms.FileInput(attrs={"class": "form-control"})
    )
    cover = forms.ImageField(
        required=False, widget=forms.FileInput(attrs={"class": "form-control"})
    )
    username = forms.CharField(
        max_length=64,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Логин",
                "class": "form-control",
                "readonly": "readonly",
            }
        ),
    )  # Изменили `disabled=True` на `readonly`, чтобы сохранить значение
    birthday = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    first_name = forms.CharField(
        required=False,
        max_length=64,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        required=False,
        max_length=64,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    middle_name = forms.CharField(
        required=False,
        max_length=64,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    phone = forms.CharField(
        required=False,
        max_length=16,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    name = forms.CharField(
        required=False,
        max_length=64,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    city = forms.CharField(
        required=False,
        max_length=64,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        max_length=64, widget=forms.EmailInput(attrs={"class": "form-control"})
    )  # Используем EmailField
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES, widget=forms.Select(attrs={"class": "form-control"})
    )
    description = forms.CharField(
        max_length=5000,
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Profile
        fields = [
            "avatar",
            "cover",
            "city",
            "username",
            "first_name",
            "last_name",
            "middle_name",
            "birthday",
            "name",
            "phone",
            "gender",
            "description",
            "email",
        ]


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = [
            "name",
            "data_start",
            "data_end",
            "time_start",
            "time_end",
            "description",
            "pagetype",
        ]


class ProductExpensePositionForm(forms.ModelForm):
    class Meta:
        model = ProductExpensePosition
        fields = [
            "name",
            "count",
        ]


class ProductExpensePurchaseForm(forms.ModelForm):
    class Meta:
        model = ProductExpensePurchase
        fields = [
            "productexpenseposition",
            "manufacturers",
            "count",
            "price",
            "data",
        ]
        widgets = {
            'data': forms.DateInput(attrs={
                'type': 'date',  # исправлено с 'data' на 'date'
                'class': 'form-control',  # добавьте класс для стилизации, если нужно
            }),
        }

    data = models.DateField(
        blank=True,
        null=True,
        verbose_name='Дата'
    )



class ExtendedSiteForm(forms.ModelForm):
    site_domain = forms.CharField(label="Домен", max_length=100, required=False)
    site_name = forms.CharField(label="Название сайта", max_length=100, required=False)

    class Meta:
        model = ExtendedSite
        fields = ["templates"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Пытаемся получить объект site, если он существует в instance
        site = self.instance.site if hasattr(self.instance, "site") else None
        if site:
            self.fields["site_domain"].initial = site.domain
            self.fields["site_name"].initial = site.name

    def save(self, commit=True):
        with transaction.atomic():
            extended_site = super().save(commit=False)
            site_domain = self.cleaned_data.get("site_domain")
            site_name = self.cleaned_data.get("site_name")

            if site_domain and site_name:
                # Получаем или создаём сайт с указанным доменом
                site, created = Site.objects.get_or_create(
                    domain=site_domain, defaults={"name": site_name}
                )
                if not created and site.name != site_name:
                    site.name = site_name
                    site.save()

                extended_site.site = site  # Присваиваем site в поле OneToOneField

            if commit:
                extended_site.save()
                self.create_related_models(extended_site)

        return extended_site

    def create_related_models(self, instance):
        # Получаем site напрямую, так как это OneToOneField
        site = instance.site
        if not site:
            print("Ошибка: instance.site отсутствует!")
            return

        print(f"Создаем связанные объекты для {site.domain}")

        # Создание SEO записей
        for page_type, page_name in Seo.PAGE_CHOICE:
            if not Seo.objects.filter(pagetype=page_type, site=site).exists():
                seo = Seo.objects.create(
                    pagetype=page_type, title=page_name
                )  # Уберите site=site, если Seo.site - M2M
                seo.site.add(site)  # Используйте .add() для M2M
                print(f"SEO запись создана для {page_name} с site={site}")
        # Создание глобальных настроек
        # Глобальные настройки
        if not SettingsGlobale.objects.filter(site=site).exists():
            SettingsGlobale.objects.create(site=site)
            print(f"Созданы глобальные настройки для {site.domain}")
        else:
            print(f"Глобальные настройки для {site.domain} уже существуют, пропускаем.")

        # Контактная страница
        if not ContactPage.objects.filter(site=site).exists():
            ContactPage.objects.create(site=site)
            print("Страница 'Контакты' создана")
        else:
            print("Страница 'Контакты' уже существует, пропускаем.")

        # Страница "О нас"
        if not AboutPage.objects.filter(site=site).exists():
            AboutPage.objects.create(site=site)
            print("Страница 'О нас' создана")
        else:
            print("Страница 'О нас' уже существует, пропускаем.")

        # Главная страница
        if not HomePage.objects.filter(site=site).exists():
            HomePage.objects.create(site=site)
            print("Главная страница создана")
        else:
            print("Главная страница уже существует, пропускаем.")

        # Создание страниц Pages, исключая pagetype=1
        for page_type, page_name in Pages.PAGETYPE:
            if page_type == 1:
                continue
            if not Pages.objects.filter(pagetype=page_type, site=site).exists():
                page = Pages.objects.create(
                    pagetype=page_type, name=page_name
                )  # Уберите site=site, если Pages.site - M2M
                page.site.add(site)  # Используйте .add() для M2M
                self.generate_slug(page)
                print(f"Страница создана: {page.name} с site={page.site}")

    def generate_slug(self, page):
        if not page.slug:
            base_slug = slugify(unidecode(page.name))
            slug = base_slug
            counter = 1
            while Pages.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            page.slug = slug
            page.save()


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["type", "chat", "products", "advertisement", "author", "description"]
        widgets = {
            "type": forms.Select(choices=Complaint.TYPE),
            "description": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Введите описание жалобы"}
            ),
        }


class ReviewsForm(forms.ModelForm):
    class Meta:
        model = Reviews
        fields = ["publishet", "text", "product", "starvalue"]
        widgets = {
            "publishet": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Введите ваш отзыв...",
                }
            ),
            "product": forms.Select(attrs={"class": "form-select"}),
            "starvalue": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "max": 5}
            ),
        }


class CategoriesForm(forms.ModelForm):
    site = forms.ModelMultipleChoiceField(
        queryset=Site.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",
                "id": "choices-multiple-site",
                "data-choices": "",
                "name": "choices-multiple-default",
                "multiple": "multiple",
            }
        ),
        required=False,
    )

    class Meta:
        model = Categories
        fields = [
            "name",
            "slug",
            "description",
            "parent",
            "cover",
            "icon",
            "image",
            "previev",
            "title",
            "metadescription",
            "site",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Название"}
            ),
            "slug": forms.TextInput(
                attrs={"class": "form-control input-default", "placeholder": "Slug"}
            ),
            "description": Textarea(
                attrs={"class": "form-control input-default", "placeholder": "Описание"}
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Заголовок",
                }
            ),
            "metadescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Мета-описание",
                }
            ),
            "propertytitle": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Заголовок",
                }
            ),
            "propertydescription": forms.Textarea(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Мета-описание",
                }
            ),
            "parent": forms.Select(
                attrs={
                    "class": "default-select form-control wide",
                    "placeholder": "Родитель",
                }
            ),
            "icon": forms.FileInput(attrs={"class": "form-file-input form-control"}),
            "image": forms.FileInput(attrs={"class": "form-file-input form-control"}),
            "cover": forms.FileInput(attrs={"class": "form-file-input form-control"}),
            "site": forms.SelectMultiple(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Генерация slug из name с помощью slugify
        instance.slug = slugify(instance.name)

        if commit:
            instance.save()
            self.cleaned_data["site"] and instance.site.set(
                self.cleaned_data["site"]
            )  # Устанавливаем ManyToMany связь
        else:
            self.save_m2m = lambda: instance.site.set(
                self.cleaned_data["site"]
            )  # Для случая commit=False

        return instance


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "type",
            "status",
            "phone_number",
            "customer_name",
            "customer_surname",
            "customer_email",
            "sflat",
            "sfloor",
            "porch",
            "user_comment",
            "requires_delivery",
            "delivery_address",
            "adress",
            "amount",
            "delivery_price",
            "all_amount",
        ]


class SelectedProductForm(forms.ModelForm):
    class Meta:
        model = SelectedProduct
        fields = ["product", "quantity", "amount", "status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["product"].disabled = True
        self.fields["amount"].disabled = True

        # Добавляем к quantity класс и data-price для JS
        if self.instance and self.instance.product:
            price = (
                getattr(self.instance.product, "price", None) or 0
            )  # замени на нужное поле цены

            self.fields["quantity"].widget.attrs.update(
                {
                    "class": "quantity-input form-control",
                    "data-price": price,
                    "min": "0",
                }
            )
        else:
            self.fields["quantity"].widget.attrs.update(
                {
                    "class": "quantity-input form-control",
                    "data-price": "0",
                    "min": "0",
                }
            )

        # Для amount сделаем класс и disabled (он уже disabled по полю)
        self.fields["amount"].widget.attrs.update(
            {
                "class": "amount-input form-control",
                "step": "0.01",
                "readonly": True,  # readonly лучше для не редактируемого, чем disabled, если нужно отправлять значение
            }
        )


SelectedProductFormSet = forms.modelformset_factory(
    SelectedProduct, form=SelectedProductForm, extra=0, can_delete=True
)


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            "name",
            "inventory_number",
            "description",
            "purchase_date",
            "warranty_expiration",
            "is_active",
            "location",
            "responsible_person",
        ]


class AtributeForm(forms.ModelForm):
    class Meta:
        model = Atribute
        fields = ["name", "slug", "content", "image"]


class ProductsForm(forms.ModelForm):
    site = forms.ModelMultipleChoiceField(
        queryset=Site.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",
                "id": "choices-multiple-site",
                "data-choices": "",
                "name": "choices-multiple-default",
                "multiple": "multiple",
            }
        ),
        required=False,
    )
    variable = forms.ModelChoiceField(
        queryset=Variable.objects.all(), required=False, label="Вариация"
    )

    publishet = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Черновик",
    )

    posted = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="опубликован",
    )

    files = MultiFileField(
        required=False,
        max_num=10,
        attrs={"class": "form-control cursor-pointer form-file"},
    )

    class Meta:
        model = Products
        fields = "__all__"

        widgets = {
            "type": forms.Select(attrs={"class": "form-control"}),
            "typeofchoice": forms.Select(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "review_rating": forms.NumberInput(attrs={"class": "form-control"}),
            "review_count": forms.NumberInput(attrs={"class": "form-control"}),
            "review_all_sum": forms.NumberInput(attrs={"class": "form-control"}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "fragment": forms.Textarea(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control"}),
            "previev": forms.FileInput(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "metadescription": forms.Textarea(attrs={"class": "form-control"}),
            "propertytitle": forms.TextInput(attrs={"class": "form-control"}),
            "propertydescription": forms.Textarea(attrs={"class": "form-control"}),
            "category": forms.SelectMultiple(attrs={"class": "form-control"}),
            "manufacturers": forms.SelectMultiple(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "price_item": forms.Select(attrs={"class": "form-control"}),
            "costprice": forms.NumberInput(attrs={"class": "form-control"}),
            "costprice_item": forms.Select(attrs={"class": "form-control"}),
            "valute": forms.Select(attrs={"class": "form-control"}),
            "manufacturer_identifier": forms.NumberInput(
                attrs={"class": "form-control"}
            ),
            "atribute": forms.SelectMultiple(attrs={"class": "form-control"}),
            "stocks": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "order": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "review": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "faqs": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "comment": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "create": forms.DateTimeInput(attrs={"class": "form-control"}),
            "site": forms.SelectMultiple(attrs={"class": "form-control"}),
            "weight": forms.NumberInput(attrs={"class": "form-control"}),
            "width": forms.NumberInput(attrs={"class": "form-control"}),
            "height": forms.NumberInput(attrs={"class": "form-control"}),
            "length": forms.NumberInput(attrs={"class": "form-control"}),
            "cover": forms.FileInput(attrs={"class": "form-control"}),
        }

        expenses = forms.ModelMultipleChoiceField(
            queryset=ProductExpense.objects.all(),
            widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
            required=False,
            label="Расходники"
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Сделать поле name не обязательным — мы подставим его в clean()
        self.fields["name"].required = False

        # ManyToManyField: manufacturers — сделать required=False, если не обязательно
        self.fields["manufacturers"].required = False
        self.fields["manufacturers"].widget.attrs["multiple"] = "multiple"
        if 'expenses' in self.fields:
            del self.fields['expenses']
        # Формирование языковых полей
        self.language_field_map = {}

        translatable_base_fields = [
            'name',
            'fragment',
            'description',
            'title',
            'metadescription',
            'propertytitle',
            'propertydescription',
        ]

        self.language_field_map = {}

        for lang_code, lang_name in LANGUAGES:
            self.language_field_map[lang_code] = {
                "lang_name": lang_name,
                "fields": []
            }

            for base in translatable_base_fields:
                field_name = f"{base}_{lang_code}"
                self.language_field_map[lang_code]["fields"].append(field_name)

        optional_fields = [
            "quantity",
            "review_rating",
            "review_count",
            "review_all_sum",
            "manufacturer_identifier",
        ]
        for field in optional_fields:
            if field in self.fields:
                self.fields[field].required = False

        if self.instance.pk and self.instance.atribute.exists():
            first_variable = self.instance.atribute.first().variable
            self.fields["variable"].initial = first_variable
            self.fields["atribute"].queryset = Atribute.objects.filter(
                variable=first_variable
            )
        else:
            self.fields["atribute"].queryset = Atribute.objects.none()

    def clean_files(self):
        files = self.cleaned_data.get("files")
        if files:
            for file in files:
                try:
                    FileExtensionValidator(
                        allowed_extensions=["png", "webp", "jpeg", "jpg", "svg"]
                    )(file)
                except forms.ValidationError:
                    self.add_error(
                        "files", f"Файл '{file.name}' имеет недопустимое расширение."
                    )
        return files

    def save_expenses(self, product):
        # Получаем данные из POST
        expenses_data = {}
        for key, value in self.data.items():
            if key.startswith('expense_quantity_'):
                expense_id = key.replace('expense_quantity_', '')
                expenses_data[expense_id] = value

        # Удаляем старые связи
        ProductExpense.objects.filter(product=product).delete()

        # Создаем новые связи
        for expense_id, quantity in expenses_data.items():
            try:
                expense_position = ProductExpensePosition.objects.get(id=expense_id)
                ProductExpense.objects.create(
                    product=product,
                    productexpenseposition=expense_position,
                    count=quantity
                )
            except (ProductExpensePosition.DoesNotExist, ValueError):
                # Пропускаем невалидные ID
                continue


    def save(self, commit=True):
        instance = super().save(commit=False)

        if not instance.slug:
            instance.slug = slugify(instance.name or "")

        if commit:
            instance.save()
            self.cleaned_data.get("site") and instance.site.set(
                self.cleaned_data["site"]
            )
            self.save_expenses(instance)

        else:
            self.save_m2m = lambda: instance.site.set(self.cleaned_data["site"])

        return instance


class ProductsVariableForm(forms.ModelForm):
    variable = forms.ModelChoiceField(
        queryset=Variable.objects.all(), required=False, label="Вариация"
    )

    class Meta:
        model = ProductsVariable
        fields = [
            "name",
            "price",
            "quantity",
            "defaultposition",
            "variable",
            "attribute",
            "site",
            "image",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "defaultposition": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "attribute": forms.SelectMultiple(attrs={"class": "form-control"}),
            "site": forms.SelectMultiple(attrs={"class": "form-control"}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Правильное обращение к полю `attribute`, а не `atribute`
        if self.instance.pk and self.instance.attribute.exists():
            first_variable = self.instance.attribute.first().variable
            self.fields["variable"].initial = first_variable
            self.fields["attribute"].queryset = Atribute.objects.filter(
                variable=first_variable
            )
        else:
            self.fields["attribute"].queryset = Atribute.objects.none()


ProductsVariableFormSet = forms.modelformset_factory(
    ProductsVariable, form=ProductsVariableForm, extra=0, can_delete=True
)


DAYS_OF_WEEK_CHOICES = [
    ('Monday', 'Понедельник'),
    ('Tuesday', 'Вторник'),
    ('Wednesday', 'Среда'),
    ('Thursday', 'Четверг'),
    ('Friday', 'Пятница'),
    ('Saturday', 'Суббота'),
    ('Sunday', 'Воскресенье'),
]

class ImportHistoryForm(forms.ModelForm):
    days_of_week = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK_CHOICES,
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select select2-multiple',
            'id': 'id_days_of_week',
            'style': 'width: 100%;',  # важно для корректного размера
        }),
        label='Дни недели'
    )

    class Meta:
        model = ImportHistory
        fields = [
            'file', 'file_url', 'file_type', 'scheduled_time', 'schedule_type',
            'daily_time', 'days_of_week', 'shop_id', 'custom_dates'
        ]
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'form-control', 'id': 'id_file', 'accept': '.csv,.xlsx,.xls,.xml'}),
            'file_url': forms.URLInput(attrs={'class': 'form-control', 'id': 'id_file_url'}),
            'file_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_file_type'}),
            'scheduled_time': forms.DateTimeInput(attrs={'class': 'form-control', 'id': 'id_scheduled_time', 'type': 'datetime-local'}),
            'schedule_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_schedule_type'}),
            'daily_time': forms.TimeInput(attrs={'class': 'form-control', 'id': 'id_daily_time', 'type': 'time'}),
                        'custom_dates': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_custom_dates',
                'autocomplete': 'off',
                'placeholder': 'Выберите даты через календарь'
            }),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.days_of_week:
            self.initial['days_of_week'] = self.instance.days_of_week.split(',')

    def clean_days_of_week(self):
        data = self.cleaned_data.get('days_of_week')
        if data:
            return ','.join(data)
        return ''


class SettingsModerationForm(forms.ModelForm):
    class Meta:
        model = SettingsModeration
        fields = '__all__'
        widgets = {
            'types': CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }

    buttom = forms.CharField(
        label="Кнопка",
        widget=forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        required=False
    )

    siddebar = forms.CharField(
        label="Сайдбар",
        widget=forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Убрать .form-control у чекбоксов
        for name, field in self.fields.items():
            if name != 'types':
                field.widget.attrs.update({'class': 'form-control'})


class LessonForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = Lesson
        fields = [
            "name",
            "resources",
            "description",
            "slug",
            "previev",
            "cover",
            "image",
            "title",
            "metadescription",
            "propertytitle",
            "propertydescription",
            "owner",
            "assistant",
            "manufacturers",
            "time",
            "price",
            "public",
            "publishet",
            "quantity_files",
            "quantity_tests",
            "quantity_video",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Исключения
        checkbox_fields = ["public", "publishet"]

        for name, field in self.fields.items():
            if name not in checkbox_fields:
                field.widget.attrs["class"] = "form-control"

        # Скрываем поле owner
        self.fields["owner"].widget = forms.HiddenInput()


class EmailTemplateForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget(), label="Содержание (HTML)")

    class Meta:
        model = EmailTemplate
        fields = ['name', 'subject', 'slug', 'category', 'content', 'plain_content', 'is_active', 'variables']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Приветственное письмо'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Тема письма'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'welcome_email'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'plain_content': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Текстовая версия письма'}),
            'variables': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                               'placeholder': '["username", "site_name", "confirmation_link"]'}),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if EmailTemplate.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Шаблон с таким slug уже существует")
        return slug


class SendEmailForm(forms.Form):
    recipient_type = forms.ChoiceField(
        choices=[('single', 'Одному получателю'), ('multiple', 'Нескольким'), ('group', 'Группе пользователей')],
        widget=forms.RadioSelect,
        initial='single'
    )
    recipient_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    recipient_emails = forms.CharField(required=False, widget=forms.Textarea(
        attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'email1@example.com\nemail2@example.com'}))
    user_group = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'form-control'}))

    subject = forms.CharField(max_length=500, widget=forms.TextInput(attrs={'class': 'form-control'}))
    content = forms.CharField(widget=CKEditorWidget())
    template = forms.ModelChoiceField(queryset=EmailTemplate.objects.filter(is_active=True), required=False,
                                      widget=forms.Select(attrs={'class': 'form-control'}))

    send_now = forms.BooleanField(required=False, initial=True, label="Отправить сейчас")
    scheduled_time = forms.DateTimeField(required=False, widget=forms.DateTimeInput(
        attrs={'class': 'form-control', 'type': 'datetime-local'}))

    has_attachments = forms.BooleanField(required=False, label="Добавить вложения")
    attachment = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        label='Вложение',
        help_text='Максимальный размер файла: 10MB',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'],
                message='Неподдерживаемый тип файла'
            )
        ]
    )

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment and attachment.size > 10 * 1024 * 1024:
            raise forms.ValidationError('Размер файла не должен превышать 10MB')
        return attachment


    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get('recipient_type')

        if recipient_type == 'single' and not cleaned_data.get('recipient_email'):
            raise forms.ValidationError("Укажите email получателя")
        elif recipient_type == 'multiple' and not cleaned_data.get('recipient_emails'):
            raise forms.ValidationError("Укажите email получателей")

        send_now = cleaned_data.get('send_now')
        scheduled_time = cleaned_data.get('scheduled_time')

        if not send_now and not scheduled_time:
            raise forms.ValidationError("Укажите время отложенной отправки")

        return cleaned_data


class EmailTemplateFilterForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Поиск по названию'}))
    category = forms.ChoiceField(required=False, choices=[('', 'Все категории')] + EmailTemplate.CATEGORY_CHOICES,
                                 widget=forms.Select(attrs={'class': 'form-control'}))
    is_active = forms.ChoiceField(required=False, choices=[('', 'Все'), ('true', 'Активные'), ('false', 'Неактивные')],
                                  widget=forms.Select(attrs={'class': 'form-control'}))


class PhoneNumberForm(forms.ModelForm):
    class Meta:
        model = PhoneNumber
        fields = ['number', 'extension', 'owner', 'department', 'status',
                  'sip_login', 'sip_password', 'sip_server', 'is_primary', 'is_ivr', 'ivr_menu']
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'}),
            'extension': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '101'}),
            'owner': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'sip_login': forms.TextInput(attrs={'class': 'form-control'}),
            'sip_password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'sip_server': forms.TextInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_ivr': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ivr_menu': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

    def clean_number(self):
        number = self.cleaned_data.get('number')
        # Валидация номера
        import re
        if not re.match(r'^\+?[0-9\s\-\(\)]{10,20}$', number):
            raise forms.ValidationError("Неверный формат номера")
        return number


class CallQueueForm(forms.ModelForm):
    class Meta:
        model = CallQueue
        fields = ['name', 'extension', 'strategy', 'timeout', 'max_wait_time',
                  'music_on_hold', 'members', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'extension': forms.TextInput(attrs={'class': 'form-control'}),
            'strategy': forms.Select(attrs={'class': 'form-control'}),
            'timeout': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_wait_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'music_on_hold': forms.FileInput(attrs={'class': 'form-control'}),
            'members': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 10}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class VoiceMenuForm(forms.ModelForm):
    class Meta:
        model = VoiceMenu
        fields = ['name', 'extension', 'greeting_message', 'greeting_audio',
                  'menu_items', 'timeout', 'max_retries', 'invalid_action', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'extension': forms.TextInput(attrs={'class': 'form-control'}),
            'greeting_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'greeting_audio': forms.FileInput(attrs={'class': 'form-control'}),
            'menu_items': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'timeout': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_retries': forms.NumberInput(attrs={'class': 'form-control'}),
            'invalid_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CallSettingsForm(forms.ModelForm):
    class Meta:
        model = CallSettings
        fields = ['extension', 'mobile_forward', 'email_forward', 'notify_on_call',
                  'notify_on_missed', 'notify_by_email', 'notify_by_sms',
                  'auto_record', 'record_outbound', 'record_inbound',
                  'work_start', 'work_end', 'work_days', 'is_online',
                  'dnd_mode', 'away_message']
        widgets = {
            'extension': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile_forward': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'}),
            'email_forward': forms.EmailInput(attrs={'class': 'form-control'}),
            'notify_on_call': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_missed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_by_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_by_sms': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_record': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'record_outbound': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'record_inbound': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'work_start': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'work_end': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'work_days': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'is_online': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'dnd_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'away_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CallFilterForm(forms.Form):
    """Форма фильтрации звонков"""
    direction = forms.ChoiceField(required=False, choices=[('', 'Все')] + CallRecord.DIRECTION_CHOICES,
                                  widget=forms.Select(attrs={'class': 'form-control'}))
    status = forms.ChoiceField(required=False, choices=[('', 'Все')] + CallRecord.STATUS_CHOICES,
                               widget=forms.Select(attrs={'class': 'form-control'}))

    caller = forms.CharField(required=False,
                             widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Номер звонящего'}))
    callee = forms.CharField(required=False,
                             widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Номер получателя'}))

    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    duration_min = forms.IntegerField(required=False, widget=forms.NumberInput(
        attrs={'class': 'form-control', 'placeholder': 'Мин. длительность (сек)'}))
    duration_max = forms.IntegerField(required=False, widget=forms.NumberInput(
        attrs={'class': 'form-control', 'placeholder': 'Макс. длительность (сек)'}))

    operator = forms.ModelChoiceField(queryset=User.objects.filter(is_staff=True), required=False,
                                      widget=forms.Select(attrs={'class': 'form-control'}), label="Оператор")


class QuickCallForm(forms.Form):
    """Форма быстрого звонка"""
    number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Введите номер телефона',
        'id': 'quickCallNumber'
    }))

    extension = forms.CharField(required=False, max_length=10, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Внутренний номер (опционально)'
    }))


class CallNoteForm(forms.ModelForm):
    """Форма добавления заметки к звонку"""

    class Meta:
        model = CallRecord
        fields = ['notes', 'tags']
        widgets = {
            'notes': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Добавить заметку о звонке...'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'тег1, тег2, тег3'}),
        }

    def clean_tags(self):
        tags = self.cleaned_data.get('tags', '')
        if tags:
            return [tag.strip() for tag in tags.split(',') if tag.strip()]
        return []


class IntegrationServiceForm(forms.ModelForm):
    """Форма для интеграции"""

    class Meta:
        model = IntegrationService
        fields = ['name', 'service_type', 'code', 'logo', 'api_url', 'api_key',
                  'api_secret', 'webhook_url', 'settings', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'service_type': forms.Select(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'api_url': forms.URLInput(attrs={'class': 'form-control'}),
            'api_key': forms.TextInput(attrs={'class': 'form-control'}),
            'api_secret': forms.PasswordInput(attrs={'class': 'form-control'}),
            'webhook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'settings': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if IntegrationService.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Интеграция с таким кодом уже существует")
        return code


class MarketplaceSettingsForm(forms.ModelForm):
    """Настройки маркетплейса"""

    class Meta:
        model = IntegrationService
        fields = ['settings']
        widgets = {
            'settings': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.settings:
            self.initial['settings'] = json.dumps(self.instance.settings, ensure_ascii=False, indent=2)


class PaymentSettingsForm(forms.ModelForm):
    """Настройки платежной системы"""

    class Meta:
        model = PaymentIntegration
        fields = ['payment_type', 'merchant_id', 'secret_key', 'public_key',
                  'commission_percent', 'commission_fixed', 'auto_confirm',
                  'success_url', 'fail_url']
        widgets = {
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
            'merchant_id': forms.TextInput(attrs={'class': 'form-control'}),
            'secret_key': forms.PasswordInput(attrs={'class': 'form-control'}),
            'public_key': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'commission_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'commission_fixed': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'auto_confirm': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'success_url': forms.URLInput(attrs={'class': 'form-control'}),
            'fail_url': forms.URLInput(attrs={'class': 'form-control'}),
        }


class DeliverySettingsForm(forms.ModelForm):
    """Настройки доставки"""

    class Meta:
        model = DeliveryIntegration
        fields = ['account_number', 'warehouse_id', 'default_delivery_type',
                  'auto_create_order', 'print_label']
        widgets = {
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'warehouse_id': forms.TextInput(attrs={'class': 'form-control'}),
            'default_delivery_type': forms.TextInput(attrs={'class': 'form-control'}),
            'auto_create_order': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'print_label': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MessengerSettingsForm(forms.ModelForm):
    """Настройки мессенджера"""

    class Meta:
        model = MessengerIntegration
        fields = ['bot_token', 'bot_name', 'webhook_secret', 'notify_on_order',
                  'notify_on_payment', 'notify_on_delivery', 'auto_reply', 'welcome_message']
        widgets = {
            'bot_token': forms.TextInput(attrs={'class': 'form-control'}),
            'bot_name': forms.TextInput(attrs={'class': 'form-control'}),
            'webhook_secret': forms.TextInput(attrs={'class': 'form-control'}),
            'notify_on_order': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_payment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_delivery': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_reply': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'welcome_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AdditionalServiceForm(forms.ModelForm):
    """Форма дополнительного сервиса"""

    class Meta:
        model = AdditionalService
        fields = ['service_category', 'api_version', 'rate_limit', 'cache_enabled', 'cache_ttl']
        widgets = {
            'service_category': forms.Select(attrs={'class': 'form-control'}),
            'api_version': forms.TextInput(attrs={'class': 'form-control'}),
            'rate_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'cache_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cache_ttl': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class SyncProductsForm(forms.Form):
    """Форма синхронизации товаров"""
    marketplace = forms.ModelChoiceField(queryset=IntegrationService.objects.filter(
        service_type='marketplace', is_active=True
    ), widget=forms.Select(attrs={'class': 'form-control'}))

    sync_type = forms.ChoiceField(choices=[
        ('all', 'Все товары'),
        ('new', 'Только новые'),
        ('updated', 'Только обновленные'),
    ], widget=forms.Select(attrs={'class': 'form-control'}))

    category = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'ID категории'
    }))


class TestConnectionForm(forms.Form):
    """Форма тестирования подключения"""
    integration = forms.ModelChoiceField(queryset=IntegrationService.objects.filter(is_active=True),
                                         widget=forms.Select(attrs={'class': 'form-control'}))


class LoyaltyProgramForm(forms.ModelForm):
    """Форма программы лояльности"""

    class Meta:
        model = LoyaltyProgram
        fields = ['name', 'is_active', 'description', 'earn_rules', 'burn_rules',
                  'points_validity_days', 'min_order_amount']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'earn_rules': forms.Textarea(attrs={'class': 'form-control', 'rows': 5,
                                                'placeholder': '{"percent": 5, "fixed": 0, "min_order": 1000}'}),
            'burn_rules': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                'placeholder': '{"max_percent": 50, "min_points": 100}'}),
            'points_validity_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_order_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def clean_earn_rules(self):
        data = self.cleaned_data.get('earn_rules')
        if isinstance(data, str):
            try:
                import json
                return json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError("Неверный формат JSON")
        return data


class LoyaltyLevelForm(forms.ModelForm):
    """Форма уровня лояльности"""

    class Meta:
        model = LoyaltyLevel
        fields = ['name', 'icon', 'color', 'min_points', 'min_orders', 'min_amount',
                  'points_multiplier', 'discount_percent', 'free_delivery', 'priority_support']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ri-star-line'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'min_points': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_orders': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'points_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'free_delivery': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'priority_support': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class LoyaltyPromoCodeForm(forms.ModelForm):
    """Форма промокода"""

    class Meta:
        model = LoyaltyPromoCode
        fields = ['code', 'name', 'description', 'discount_type', 'discount_value',
                  'min_order_amount', 'max_uses', 'valid_from', 'valid_to',
                  'level_required', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'WELCOME2024'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'discount_type': forms.Select(attrs={'class': 'form-control'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_order_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_uses': forms.NumberInput(attrs={'class': 'form-control'}),
            'valid_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'level_required': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code', '').upper()
        if LoyaltyPromoCode.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Промокод с таким кодом уже существует")
        return code


class LoyaltySettingsForm(forms.ModelForm):
    """Форма настроек лояльности"""

    class Meta:
        model = LoyaltySettings
        fields = ['welcome_points', 'welcome_points_enabled', 'registration_points',
                  'birthday_points', 'birthday_points_enabled', 'review_points',
                  'review_points_enabled', 'notify_on_points_earn', 'notify_on_level_up',
                  'notify_on_points_expire']
        widgets = {
            'welcome_points': forms.NumberInput(attrs={'class': 'form-control'}),
            'welcome_points_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'registration_points': forms.NumberInput(attrs={'class': 'form-control'}),
            'birthday_points': forms.NumberInput(attrs={'class': 'form-control'}),
            'birthday_points_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'review_points': forms.NumberInput(attrs={'class': 'form-control'}),
            'review_points_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_points_earn': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_level_up': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_points_expire': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AddPointsForm(forms.Form):
    """Форма начисления баллов"""
    user = forms.ModelChoiceField(queryset=User.objects.filter(is_active=True),
                                  widget=forms.Select(attrs={'class': 'form-control'}))
    points = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    reason = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Причина начисления'}))


class LoyaltyFilterForm(forms.Form):
    """Форма фильтрации пользователей лояльности"""
    search = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Поиск по пользователю'}))
    level = forms.ModelChoiceField(required=False, queryset=LoyaltyLevel.objects.all(),
                                   widget=forms.Select(attrs={'class': 'form-control'}))
    min_points = forms.IntegerField(required=False, widget=forms.NumberInput(
        attrs={'class': 'form-control', 'placeholder': 'Мин. баллы'}))
    max_points = forms.IntegerField(required=False, widget=forms.NumberInput(
        attrs={'class': 'form-control', 'placeholder': 'Макс. баллы'}))
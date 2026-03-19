from django import forms
from moderation.models import Subscriptions
from .models import Comments
from moderation.models import Applications


class SubscriptionForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Email",
                "name": "email",
                "id": "subscribeEmail",
            }
        ),
        label="",
    )

    class Meta:
        model = Subscriptions
        fields = [
            "email",
        ]


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = ["first_name", "last_name", "email", "comment"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated:
            self.fields.pop("first_name")
            self.fields.pop("last_name")
            self.fields.pop("email")

            # Если юзер авторизован, сохраняем его в поле author
            self.instance.author = user


class CooperationForm(forms.ModelForm):
    type = forms.ChoiceField(
        choices=Applications.TYPE, initial=4, widget=forms.HiddenInput()
    )

    class Meta:
        model = Applications
        fields = [
            "type",
            "user",
            "email",
            "phone",
            "content",
            "company_name",
            "company_inn",
            "company_director",
            "company_adress",
            "company_sku",
            "company_description",
        ]
        widgets = {
            "user": forms.Select(attrs={"class": "form-control"}),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Телефон"}
            ),
            "company_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название компании"}
            ),
            "company_inn": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ИНН организации или ИП"}
            ),
            "company_director": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ФИО директора"}
            ),
            "company_adress": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Адрес"}
            ),
            "company_sku": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Количество товаров SKU в вашем каталоге",
                }
            ),
            "company_description": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Описание"}
            ),
            "type": forms.HiddenInput(),
        }

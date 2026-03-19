from django import forms
from useraccount.models import Profile
from .models import (
    Reviews,
    Products,
    Valute,
    SelectedProduct,
    Cart,
    ProductComment,
    Manufacturers,ReviewImage,
)
from payment.models import Order
from django.core.validators import FileExtensionValidator
from multiupload.fields import MultiFileField
from django.forms.widgets import ClearableFileInput

# ✅ Сначала создаём свой виджет
class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label="Загрузить CSV-файл", required=True)


class ManufacturersForm(forms.ModelForm):
    class Meta:
        model = Manufacturers
        fields = [
            "name",
            "slug",
            "image",
            "cover",
            "description",
            "previev",  # добавлено, если хочешь его видеть в форме
            "title",
            "metadescription",
            "propertytitle",
            "propertydescription",
            "email",
            "phone",
            "company_name",
            "company_inn",
            "company_director",
            "company_adress",
            "categories",
            "site",
        ]


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


SelectedProductFormSet = forms.modelformset_factory(
    SelectedProduct, form=SelectedProductForm, extra=1, can_delete=True
)





class ReviewsForm(forms.ModelForm):
    text = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            "placeholder": "Отзыв",
            "id": "message",
            "class": "form-control"
        }),
    )
    starvalue = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={
            "id": "reiting",
            "class": "rating",
            "type": "number",
            "name": "quantity",
            "max": "5",
            "min": "0",
            "value": "0",
            "data-size": "lg",
        }),
    )
    author = forms.ModelChoiceField(
        widget=forms.HiddenInput(),
        queryset=Profile.objects.all(),
        required=False
    )
    product = forms.ModelChoiceField(
        widget=forms.HiddenInput(),
        queryset=Products.objects.all(),
        required=True
    )

    images = forms.FileField(
        widget=MultipleFileInput(attrs={"multiple": True}),
        required=False,
        label="Загрузить изображения",
    )

    class Meta:
        model = Reviews
        fields = ["text", "author", "product", "starvalue"]

    def clean_images(self):
        """Не ругаться, если файлов нет, и валидировать выбранные"""
        files = self.files.getlist("images")
        if not files:
            return None

        max_files = 5
        max_size = 5 * 1024 * 1024  # 5 MB
        if len(files) > max_files:
            raise forms.ValidationError(f"Максимум файлов: {max_files}")
        for f in files:
            if not f.content_type.startswith("image/"):
                raise forms.ValidationError(f"Файл {f.name} не является изображением")
            if f.size > max_size:
                raise forms.ValidationError(f"Файл {f.name} превышает 5 МБ")
        return files

    def save(self, commit=True):
        review = super().save(commit=commit)
        files = self.cleaned_data.get("images") or []
        for f in files:
            ReviewImage.objects.create(review=review, image=f)
        return review


class OrderLookupForm(forms.Form):
    q = forms.CharField(
        label="Номер заказа / телефон / email / ключ",
        required=True,
        widget=forms.TextInput(attrs={
            "placeholder": "Введите № заказа, телефон, email или ключ",
            "class": "form-control"
        })
    )
    def clean(self):
        data = super().clean()
        q = (data.get("q") or "").strip()
        import re
        phone = re.sub(r"[^\d]", "", q)  # только цифры
        data["q_normalized"] = q
        data["q_lower"] = q.lower()
        data["phone_digits"] = phone
        data["q_is_digit"] = q.isdigit()
        return data


class SelectedProductForm(forms.ModelForm):
    class Meta:
        model = SelectedProduct
        fields = ["product", "quantity", "session_key", "amount"]

    # Возможные валидации, если необходимо
    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity < 0:
            raise forms.ValidationError("Quantity cannot be negative")
        return quantity


# Форма для работы с Cart
class CartForm(forms.ModelForm):
    class Meta:
        model = Cart
        fields = ["user", "selectedproduct", "amount"]

    # Опциональная валидация или переопределение поведения, например:
    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount < 0:
            raise forms.ValidationError("Amount cannot be negative")
        return amount


class ProductCommentForm(forms.ModelForm):
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
        model = ProductComment
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


class UpdateCartCurrencyForm(forms.Form):
    valute = forms.ModelChoiceField(
        queryset=Valute.objects.all(),
        label="Выберите валюту",
        empty_label=None,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(f"Valutes in form: {list(self.fields['valute'].queryset)}")

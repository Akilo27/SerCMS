from django import forms
from useraccount.models import Cards, Profile, PersonalGroups
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

User = get_user_model()


class AddUserForm(forms.Form):
    identifier = forms.CharField(label="Введите username или email", required=True)


class SignUpForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Пароль", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    referrale_code = forms.CharField(
        label='Реферальный код (необязательно)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите код пригласившего вас пользователя'
        })
    )

    class Meta:
        model = Profile
        fields = ["username", "email", "password1", "password2", "referrale_code"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not field.widget.attrs.get("class"):
                field.widget.attrs["class"] = "form-control"
            else:
                field.widget.attrs["class"] += " form-control"

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if Profile.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if Profile.objects.filter(username=username).exists():
            raise ValidationError("Пользователь с таким именем уже существует.")
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.referral_code = None  # Устанавливаем личный реферальный код как пустой (может быть сгенерирован позже)

        if commit:
            user.save()
            referral_code = self.cleaned_data.get("referral_code")
            if referral_code:
                try:
                    referrer = Profile.objects.get(referral_code=referral_code)
                    user.referral = referrer
                    user.save()
                except Profile.DoesNotExist:
                    print("Реферальный код не найден")
        return user


class SignUpClientForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Пароль", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    is_company = forms.BooleanField(
        required=False, label="Компания", widget=forms.CheckboxInput()
    )

    class Meta:
        model = Profile
        fields = ["username", "email", "password1", "password2", "is_company"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not field.widget.attrs.get("class"):
                field.widget.attrs["class"] = "form-control"
            else:
                field.widget.attrs["class"] += " form-control"

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if Profile.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if Profile.objects.filter(username=username).exists():
            raise ValidationError("Пользователь с таким именем уже существует.")
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.referral_code = None  # Устанавливаем личный реферальный код как пустой (может быть сгенерирован позже)

        if commit:
            user.save()
            referral_code = self.cleaned_data.get("referral_code")
            if referral_code:
                try:
                    referrer = Profile.objects.get(referral_code=referral_code)
                    user.referral = referrer
                    user.save()
                except Profile.DoesNotExist:
                    print("Реферальный код не найден")
        return user


class UserProfileForm(forms.ModelForm):
    GENDER_CHOICES = [
        (1, "Мужской"),
        (2, "Женский"),
    ]
    TYPE_CHOICES = [
        (1, "Обычный"),
        (2, "Юр лицо"),
    ]

    # Поля профиля
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control cursor-pointer"}),
    )
    username = forms.CharField(
        max_length=64,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Логин"}),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Email"}
        ),
    )
    first_name = forms.CharField(
        required=False,
        max_length=64,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Имя"}),
    )
    last_name = forms.CharField(
        required=False,
        max_length=64,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Фамилия"}
        ),
    )
    middle_name = forms.CharField(
        required=False,
        max_length=64,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Отчество"}
        ),
    )
    phone = forms.CharField(
        required=False,
        max_length=64,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Телефон"}
        ),
    )
    birthday = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    city = forms.CharField(
        required=False,
        max_length=64,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Город"}),
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES, widget=forms.Select(attrs={"class": "form-control"})
    )

    # Поля паспорта
    passport_issued_by_whom = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Кем выдан"}
        ),
    )
    passport_date_of_issue = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    passport_the_sub_division_code = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Код подразделения"}
        ),
    )
    passport_series_and_number = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Серия и номер паспорта"}
        ),
    )
    passport_place_of_birth = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": "Место рождения"}
        ),
    )
    passport_registration = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": "Прописка"}
        ),
    )
    passport_image_1 = forms.ImageField(
        required=False, widget=forms.FileInput(attrs={"class": "form-control"})
    )
    passport_image_2 = forms.ImageField(
        required=False, widget=forms.FileInput(attrs={"class": "form-control"})
    )

    # Поля организации
    company_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Название организации"}
        ),
    )
    company_director = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Руководитель"}
        ),
    )
    company_address = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Юридический адрес"}
        ),
    )
    company_nalogovaya = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Налоговый орган"}
        ),
    )
    company_ogrn = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ОГРН"}),
    )
    company_inn = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ИНН"}),
    )
    company_kpp = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "КПП"}),
    )
    company_data_registration = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    company_type_activity = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": "Основной вид деятельности"}
        ),
    )

    class Meta:
        model = Profile
        fields = [
            # Профиль
            "avatar",
            "username",
            "first_name",
            "last_name",
            "middle_name",
            "email",
            "phone",
            "birthday",
            "city",
            "adresses",
            "gender",
            # Паспортные данные
            "passport_issued_by_whom",
            "passport_date_of_issue",
            "passport_the_sub_division_code",
            "passport_series_and_number",
            "passport_place_of_birth",
            "passport_registration",
            "passport_image_1",
            "passport_image_2",
            # Организация
            "company_name",
            "company_director",
            "company_address",
            "company_nalogovaya",
            "company_ogrn",
            "company_inn",
            "company_kpp",
            "company_data_registration",
            "company_type_activity",
        ]


class CustomAuthenticationForm(forms.Form):
    identifier = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Введите логин, email или телефон",
            }
        ),
        label="Логин, Email или Телефон",
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Введите пароль"}
        ),
        label="Пароль",
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get("identifier")
        password = cleaned_data.get("password")

        if not identifier or not password:
            raise forms.ValidationError("Введите логин/Email/телефон и пароль.")

        # Пытаемся найти пользователя по логину, email или телефону
        user = None
        try:
            if "@" in identifier:  # Проверяем, если это email
                user = User.objects.get(email=identifier)
            elif identifier.isdigit():  # Если это телефон
                user = User.objects.get(phone=identifier)
            else:  # В остальных случаях предполагаем, что это username
                user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            raise forms.ValidationError("Пользователь не найден.")

        # Аутентификация пользователя
        self.user = authenticate(
            self.request, username=user.username, password=password
        )
        if self.user is None:
            raise forms.ValidationError("Неправильный логин или пароль.")

        return cleaned_data

    def get_user(self):
        return self.user


class PasswordChangeCustomForm(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )


class PasswordResetEmailForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={
            "autocomplete": "email",
            "class": "form-control",  # Добавляем класс Bootstrap
            "placeholder": "Введите email"  # Добавляем placeholder
        }),
    )

class SetPasswordFormCustom(SetPasswordForm):
    new_password1 = forms.CharField(label="New password", widget=forms.PasswordInput)
    new_password2 = forms.CharField(
        label="New password confirmation", widget=forms.PasswordInput
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].widget.attrs.update(
            {"autocomplete": "new-password"}
        )
        self.fields["new_password2"].widget.attrs.update(
            {"autocomplete": "new-password"}
        )


class CardsForm(forms.ModelForm):
    class Meta:
        model = Cards
        fields = ["card", "status"]
        widgets = {
            "card": forms.TextInput(
                attrs={
                    "class": "form-control input-default",
                    "placeholder": "Номер карты",
                }
            ),
            "user": forms.Select(
                attrs={
                    "class": "default-select form-control wide",
                    "placeholder": "Пользователь",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "default-select form-control wide",
                    "placeholder": "Статус",
                }
            ),
        }


User = get_user_model()  # Модель пользователей, если вы используете кастомную


class PersonalGroupForm(forms.ModelForm):
    class Meta:
        model = PersonalGroups
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

        # Если у текущего экземпляра уже есть company (случай UpdateView),
        # то ограничиваем пользователей только теми, кто принадлежит этой компании
        if self.instance and self.instance.company_id:
            self.fields["users"].queryset = self.instance.company.users.all()
        else:
            # При создании (CreateView), если ещё не указана company,
            # оставляем пустую выборку
            self.fields["users"].queryset = User.objects.none()

from django import forms
from .models import Lead
from django.contrib.auth import get_user_model
import uuid
from useraccount.models import Profile

User = get_user_model()


class LeadForm(forms.ModelForm):
    client = forms.CharField(
        required=False, widget=forms.HiddenInput(attrs={"id": "id_client"})
    )
    users = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Lead
        fields = ["name", "description", "image", "amount", "client", "users"]

    def clean_client(self):
        client_id = self.cleaned_data.get("client")

        # Если пустое или техническое значение — вернём None
        if client_id in [None, "", "undefined", "null"]:
            return None

        try:
            client_uuid = uuid.UUID(client_id)
            client = Profile.objects.get(id=client_uuid)
            # Только если это клиент (type=4), возвращаем
            if client.type == 4:
                return client
            return None  # если не клиент — считаем, что не задан
        except (ValueError, Profile.DoesNotExist):
            return None  # если ID невалиден или не найден — считаем, что не задан

    def clean_users(self):
        users_str = self.cleaned_data.get("users", "")
        user_ids = [
            uid.strip()
            for uid in users_str.split(",")
            if self._is_valid_uuid(uid.strip())
        ]
        users = User.objects.filter(id__in=user_ids)
        return users

    def _is_valid_uuid(self, val):
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.client = self.cleaned_data.get("client")

        # Устанавливаем явно все поля, которые могут не сохраниться
        instance.name = self.cleaned_data.get("name")
        instance.description = self.cleaned_data.get("description")
        instance.image = self.cleaned_data.get("image")
        instance.amount = self.cleaned_data.get("amount")

        if commit:
            instance.save()
            self.save_m2m()

        return instance

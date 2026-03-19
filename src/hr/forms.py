from django import forms
from .models import VacancyResponse, WorkShift


class VacancyResponseForm(forms.ModelForm):
    class Meta:
        model = VacancyResponse
        fields = ["full_name", "email", "phone", "message", "resume"]

class WorkShiftPhotoForm(forms.ModelForm):
    class Meta:
        model = WorkShift
        fields = [
            'photo_accept_place', 'photo_entry_place', 'selfie_entry', 'video_entry',
            'photo_handover_place', 'photo_exit_place', 'selfie_exit', 'video_exit',
        ]
        widgets = {
            'photo_accept_place': forms.ClearableFileInput(attrs={'multiple': False}),
            'photo_entry_place': forms.ClearableFileInput(attrs={'multiple': False}),
            'selfie_entry': forms.ClearableFileInput(attrs={'multiple': False}),
            'video_entry': forms.ClearableFileInput(attrs={'multiple': False}),
            'photo_handover_place': forms.ClearableFileInput(attrs={'multiple': False}),
            'photo_exit_place': forms.ClearableFileInput(attrs={'multiple': False}),
            'selfie_exit': forms.ClearableFileInput(attrs={'multiple': False}),
            'video_exit': forms.ClearableFileInput(attrs={'multiple': False}),
        }


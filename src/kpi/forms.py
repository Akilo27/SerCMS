from django import forms
from .models import EmployeePosition

class EmployeePositionForm(forms.ModelForm):
    class Meta:
        model = EmployeePosition
        fields = '__all__'
        widgets = {
            'Bonuses': forms.SelectMultiple(attrs={
                'class': 'form-select select2-multiple',
                'data-placeholder': 'Выберите бонусы'
            }),
            'Prizes': forms.SelectMultiple(attrs={
                'class': 'form-select select2-multiple',
                'data-placeholder': 'Выберите премии'
            }),
            'Penalties': forms.SelectMultiple(attrs={
                'class': 'form-select select2-multiple',
                'data-placeholder': 'Выберите штрафы'
            }),
        }
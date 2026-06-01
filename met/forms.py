from django import forms
from .models import User, Request

class RegistrationForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput(), label="Подтвердите пароль")

    class Meta:
        model = User
        fields = ['fio', 'phone', 'password_hash']
        widgets = {
            'password_hash': forms.PasswordInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password_hash") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Пароли не совпадают")
        return cleaned_data


class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        # Поля, которые пользователь заполняет на сайте
        fields = ['address', 'total_sum']

        # 1. Meta widgets: кастомизация внешнего вида полей
        widgets = {
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите адрес объекта демонтажа'
            }),
            'total_sum': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ожидаемая сумма'
            }),
        }

    # 2. Пример clean_<fieldname>(): валидация конкретного поля
    def clean_total_sum(self):
        total_sum = self.cleaned_data.get('total_sum')
        if total_sum is not None and total_sum < 0:
            raise forms.ValidationError("Сумма заявки не может быть отрицательной!")
        return total_sum
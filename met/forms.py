from django import forms
from .models import User, Request, Category, RequestPhoto, RequestItem, Request_services

class RequestItemForm(forms.ModelForm):
    class Meta:
        model = RequestItem
        fields = ['scrap_type', 'weight']
        labels = {'scrap_type': 'Тип металла', 'weight': 'Вес, кг'}


class RequestServiceForm(forms.ModelForm):
    class Meta:
        model = Request_services
        fields = ['services_id']
        labels = {'services_id': 'Услуга'}
class FeedbackForm(forms.Form):
    name = forms.CharField(max_length=100, label='Ваше имя')
    message = forms.CharField(widget=forms.Textarea, label='Сообщение')
class RequestPhotoForm(forms.ModelForm):
    class Meta:
        model = RequestPhoto
        exclude = ['request_id', 'uploaded_at']  # exclude вместо fields — оставляем всё, кроме служебных полей


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['title', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'title': 'Название категории',
            'description': 'Описание категории',
        }
        help_texts = {
            'title': 'Например: чёрный металл, цветной металл',
            'description': 'Кратко опишите, что входит в эту категорию',
        }
        error_messages = {
            'title': {
                'required': 'Название категории обязательно для заполнения',
                'max_length': 'Слишком длинное название',
            },
        }

    class Media:
        css = {'all': ('css/category_form.css',)}
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
        fields = ['address', 'act_document']

        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'act_document': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    # 2. Пример clean_<fieldname>(): валидация конкретного поля
    def clean_address(self):
        address = self.cleaned_data.get('address')
        if len(address.strip()) < 5:
            raise forms.ValidationError("Укажите полный адрес (минимум 5 символов)")

        # Проверка: нет ли уже активной (не завершённой/не отменённой) заявки по этому адресу
        active_statuses = ['new', 'in_progress']
        duplicate = Request.objects.filter(
            address__iexact=address.strip(),
            status__in=active_statuses
        ).exists()
        if duplicate:
            raise forms.ValidationError("По этому адресу уже есть активная заявка")

        return address
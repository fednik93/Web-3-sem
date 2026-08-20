from django.db import models
from django.utils import timezone
from django.urls import reverse

class NewRequestManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='new')
class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'
class User(models.Model):
    id = models.AutoField(primary_key=True)
    fio = models.CharField(max_length=255, verbose_name='ФИО')
    phone = models.CharField(max_length=12, unique=True, verbose_name='Номер телефона')
    password_hash = models.CharField(max_length=255, verbose_name='Пароль')
    role_id = models.ForeignKey(Role, on_delete=models.PROTECT, verbose_name='Роль')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания пользователя')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Время обновления пользователя')

    objects = models.Manager()

    def __str__(self):
        return self.fio
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
class Category(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')

    def __str__(self):
        return f"{self.title}"
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
class ScrapType(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, verbose_name='Название')
    price_per_kg = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Цена за кг')
    category_id = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='Категория')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления цен')
    def __str__(self):
        return self.title
    class Meta:
        verbose_name = 'Тип металла'
        verbose_name_plural = 'Типы металла'
class Request(models.Model):
    statuses = [
        ('new', 'Новая'),
        ('in_progress', 'В процессе'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена')
    ]
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.PROTECT, related_name='users', verbose_name='ID пользователя')
    address = models.CharField(max_length=255, verbose_name='Адрес клиента')
    status = models.CharField(max_length=255, choices=statuses, default='new', verbose_name='Статус заказа')
    total_sum = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Итоговая сумма')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Время подачи заявки')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Время смены статуса заказа')

    objects = models.Manager()
    new_requests = NewRequestManager()
    scrap_types = models.ManyToManyField(ScrapType, through='RequestItem', verbose_name="Компоненты лома")

    def __str__(self):
        return f"Заявка #{self.id} - {self.address}"
    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']

    def get_absolute_url(self):
        # 'request_detail' — это имя (name) пути из urls.py
        return reverse('request_detail', args=[str(self.id)])
class RequestPhoto(models.Model):
    id = models.AutoField(primary_key=True)
    request_id = models.ForeignKey(Request, on_delete=models.CASCADE, verbose_name='Id запроса')
    photo = models.ImageField(upload_to='photos/', null=True, blank=True, verbose_name='Фото лома')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Время загрузки фото')

    def __str__(self):
        return f"Фото к заявке {self.request_id}"
    class Meta:
        verbose_name = 'Фото к заявке'
        verbose_name_plural = 'Фото к заявкам'
class Service(models.Model):
    id = models.AutoField(primary_key=True)
    service_name = models.CharField(max_length=255, verbose_name='Название услуги')
    base_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Цена услуги')

    def __str__(self):
        return f" {self.service_name} - {self.base_price}"
    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
class Request_services(models.Model):
    id = models.AutoField(primary_key=True)
    request_id = models.ForeignKey(Request, on_delete=models.CASCADE, verbose_name='ID запроса')
    services_id = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name='ID услуги')

    def __str__(self):
        return f"{self.request_id} {self.services_id}"
    class Meta:
        verbose_name = 'Услуга в заявке'
        verbose_name_plural = 'Услуги в заявке'


class RequestItem(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    scrap_type = models.ForeignKey(ScrapType, on_delete=models.CASCADE)
    weight = models.PositiveIntegerField(verbose_name="Вес в кг")  # Доп. поле!

    # 3. Использование переопределенного метода save() в модели
    def save(self, *args, **kwargs):
        # Логика: перед сохранением элемента связи можем что-то автоматически посчитать
        super().save(*args, **kwargs)  # Сначала сохраняем саму запись

        # Например, автоматически обновляем total_sum в родительской заявке
        parent_request = self.request
        # Простой пример автоматического расчета (расширить можно через агрегацию)
        parent_request.total_sum = self.weight * self.scrap_type.price_per_kg
        parent_request.save()
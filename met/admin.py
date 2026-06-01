from django.contrib import admin
from .models import Category, Request, RequestPhoto, Role, Service, ScrapType, User, Request_services
admin.site.register(Role)
admin.site.register(Category)
admin.site.register(Service)
class RequestPhotoInline(admin.TabularInline):
    model = RequestPhoto
    extra = 1
class RequestServiceInline(admin.TabularInline):
    model = Request_services
    extra = 1

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'fio_with_phone', 'role_id', 'created_at', 'updated_at')
    list_display_links = ('id', 'fio_with_phone')
    search_fields = ('fio', 'phone')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    @admin.display(description='Данные клиента')
    def fio_with_phone(self, obj):
        return f"{obj.fio} - {obj.phone}"

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'address', 'status', 'total_sum', 'created_at')
    list_display_links = ('user_id', 'status')
    search_fields = ('user__fio', 'address')
    date_hierarchy = 'created_at'
    list_filter = ('status', 'created_at')
    raw_id_fields = ('user_id',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [RequestPhotoInline, RequestServiceInline]

@admin.register(ScrapType)
class ScrapTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'category_id', 'price_per_kg', 'updated_status')
    list_filter = ('category_id',)
    search_fields = ('title',)
    def updated_status(self, obj):
        return f"Обновлено {obj.updated_at.strftime('%d.%m')}"
    updated_status.short_description = 'Дата обновления'

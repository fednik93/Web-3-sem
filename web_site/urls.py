"""
URL configuration for web_site project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from met import views
from django.conf import settings
from django.conf.urls.static import static
import debug_toolbar
urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('requests/', views.request_list, name='request_list'),
    path('requests/create/', views.request_create, name='request_create'),
    path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    path('requests/<int:pk>/edit/', views.request_edit, name='request_edit'),
    path('requests/<int:pk>/delete/', views.request_delete, name='request_delete'),
    path('orm-demo/', views.orm_demo, name='orm_demo'),
    path('feedback/', views.feedback, name='feedback'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('requests/<int:pk>/photo/', views.request_photo_upload, name='request_photo_upload'),
    path('logout/', views.logout_view, name='logout'),
    path('requests/<int:pk>/items/<int:item_id>/delete/', views.request_item_delete, name='request_item_delete'),
    path('requests/<int:pk>/services/<int:service_id>/delete/', views.request_service_delete, name='request_service_delete'),

    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
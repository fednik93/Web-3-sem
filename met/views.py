from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum
from .models import Request, User, Role, Category, ScrapType, RequestPhoto
from django.shortcuts import redirect
from .forms import RegistrationForm, RequestForm, FeedbackForm, RequestPhotoForm, CategoryForm
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponseRedirect
from django.urls import reverse
def orm_demo(request):
    # Chaining filters — фильтры цепочкой
    chained = ScrapType.objects.filter(price_per_kg__gt=1).filter(category_id__title__icontains='метал')

    # __icontains (без учёта регистра) и __contains (с учётом регистра, зависит от БД)
    icontains_categories = Category.objects.filter(title__icontains='метал')
    contains_categories = Category.objects.filter(title__contains='Метал')

    # Limiting QuerySets — срез
    limited_scrap_types = ScrapType.objects.order_by('-price_per_kg')[:3]

    # values() / values_list()
    values_result = ScrapType.objects.values('title', 'price_per_kg')[:5]
    values_list_result = ScrapType.objects.values_list('title', flat=True)[:5]

    # count(), exists() — быстрее, чем len(queryset) или if queryset
    total_scrap_types = ScrapType.objects.count()
    has_expensive = ScrapType.objects.filter(price_per_kg__gt=1000).exists()

    updated_count = None
    deleted_count = None
    if request.method == 'POST':
        if 'run_update' in request.POST:
            # update() — массовое обновление одним SQL-запросом, без save() на каждом объекте
            updated_count = Request.objects.filter(status='new').update(status='in_progress')
        elif 'run_delete' in request.POST:
            # delete() — массовое удаление отфильтрованного набора
            deleted_info = RequestPhoto.objects.filter(photo='').delete()
            deleted_count = deleted_info[0]
        return HttpResponseRedirect(reverse('orm_demo'))

    context = {
        'chained': chained,
        'icontains_categories': icontains_categories,
        'contains_categories': contains_categories,
        'limited_scrap_types': limited_scrap_types,
        'values_result': values_result,
        'values_list_result': values_list_result,
        'total_scrap_types': total_scrap_types,
        'has_expensive': has_expensive,
        'updated_count': updated_count,
        'deleted_count': deleted_count,
    }
    return render(request, 'orm_demo.html', context)
# views.py
def feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            # form.cleaned_data — доступ к провалидированным и приведённым к типу данным
            name = form.cleaned_data['name']
            message = form.cleaned_data['message']
            messages.success(request, f"Спасибо, {name}! Ваше сообщение принято.")
            return HttpResponseRedirect(reverse('feedback'))  # HttpResponseRedirect вместо shortcuts.redirect
    else:
        form = FeedbackForm()
    return render(request, 'feedback.html', {'form': form})
def request_photo_upload(request, pk):
    request_obj = get_object_or_404(Request, pk=pk)
    if request.method == 'POST':
        form = RequestPhotoForm(request.POST, request.FILES)  # request.FILES обязателен для файловых полей
        if form.is_valid():
            photo = form.save(commit=False)
            photo.request_id = request_obj
            photo.save()
            return HttpResponseRedirect(reverse('request_detail', args=[pk]))
    else:
        form = RequestPhotoForm()
    return render(request, 'request_photo_form.html', {'form': form, 'request_obj': request_obj})


def category_list(request):
    categories = Category.objects.all()
    return render(request, 'category_list.html', {'categories': categories})


def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('category_list'))
    else:
        form = CategoryForm()
    return render(request, 'category_form.html', {'form': form})
def request_list(request):
    queryset = Request.objects.select_related('user_id') \
        .prefetch_related('scrap_types') \
        .exclude(status='completed') \
        .order_by('-total_sum')

    name_query = request.GET.get('fio')
    if name_query:
        queryset = queryset.filter(user_id__fio__icontains=name_query)

    # Агрегирование: считаем общую сумму ТОЛЬКО для отфильтрованных заявок
    total_revenue = queryset.aggregate(total=Sum('total_sum'))['total'] or 0

    # Пагинация (передаем наш оптимизированный и отфильтрованный queryset)
    paginator = Paginator(queryset, 5)
    page = request.GET.get('page')
    try:
        requests_page = paginator.page(page)
    except PageNotAnInteger:
        requests_page = paginator.page(1)
    except EmptyPage:
        requests_page = paginator.page(paginator.num_pages)

    return render(request, 'requests.html', {
        'requests': requests_page,  # В шаблон отдаем страницу пагинатора
        'total_revenue': total_revenue
    })
def home(request):
    return redirect('request_list')

def request_detail(request, pk):
    obj = get_object_or_404(Request, pk=pk)
    return render(request, 'request_detail.html', {'request_obj': obj})

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password_hash = make_password(form.cleaned_data['password_hash'])
            client_role = Role.objects.get(name__icontains='Пользователь')
            user.role_id = client_role
            user.save()
            return redirect('login')
        else:
            print(form.errors)
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        raw_password = request.POST.get('password')

        try:
            user = User.objects.get(phone=phone)
            # Проверяем: совпадает ли введенный пароль с тем, что захеширован в базе
            if check_password(raw_password, user.password_hash):
                request.session['user_id'] = user.id
                return redirect('request_list')
            else:
                messages.error(request, "Неверный пароль")
        except User.DoesNotExist:
            messages.error(request, "Пользователь не найден")

    return render(request, 'login.html')


# CREATE (Создание) + Демонстрация save(commit=True)
def request_create(request):
    if request.method == 'POST':
        form = RequestForm(request.POST, request.FILES)
        if form.is_valid():
            user_id = request.session.get('user_id')
            if not user_id:
                return redirect('login')
            new_request = form.save(commit=False)
            new_request.user_id = get_object_or_404(User, pk=user_id)
            new_request.save()
            return redirect('request_list')
    else:
        form = RequestForm()
    return render(request, 'request_form.html', {'form': form, 'action': 'Создать'})


# UPDATE (Редактирование)
def request_edit(request, pk):
    if not request.session.get('user_id'):
        return redirect('login')
    request_obj = get_object_or_404(Request, pk=pk)
    if request.method == 'POST':
        form = RequestForm(request.POST, request.FILES, instance=request_obj)
        if form.is_valid():
            form.save()  # Здесь commit=True, сразу обновляет базу
            return redirect('request_list')
    else:
        form = RequestForm(instance=request_obj)
    return render(request, 'request_form.html', {'form': form, 'action': 'Редактировать'})


# DELETE (Удаление)
def request_delete(request, pk):
    request_obj = get_object_or_404(Request, pk=pk)
    if request.method == 'POST':
        request_obj.delete()
        return redirect('request_list')
    return render(request, 'request_confirm_delete.html', {'request_obj': request_obj})
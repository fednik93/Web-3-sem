from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, Avg, Count
from .models import Request, User, Role, Category, ScrapType, RequestPhoto, Request_services, RequestItem
from django.shortcuts import redirect
from .forms import RegistrationForm, RequestForm, FeedbackForm, RequestPhotoForm, CategoryForm, RequestServiceForm, RequestItemForm
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponseRedirect
from django.urls import reverse
def logout_view(request):
    request.session.flush()
    return redirect('home')
def orm_demo(request):
    # Chaining filters — фильтры цепочкой
    chained = ScrapType.objects.filter(price_per_kg__gt=1).filter(category_id__title__icontains='металл')

    # __icontains (без учёта регистра) и __contains (с учётом регистра, зависит от БД)
    icontains_categories = Category.objects.filter(title__icontains='металл')
    contains_categories = Category.objects.filter(title__contains='Металл')

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
    current_user = _get_current_user(request)
    if not current_user:
        return redirect('login')

    request_obj = get_object_or_404(Request, pk=pk)
    if not _is_manager(current_user) and request_obj.user_id_id != current_user.id:
        messages.error(request, "У вас нет доступа к этой заявке.")
        return redirect('request_list')

    if request.method == 'POST':
        form = RequestPhotoForm(request.POST, request.FILES)
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
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    current_user = get_object_or_404(User, pk=user_id)
    if 'менеджер' not in current_user.role_id.name.lower():
        messages.error(request, "Добавлять категории могут только менеджеры.")
        return redirect('category_list')

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('category_list'))
    else:
        form = CategoryForm()
    return render(request, 'category_form.html', {'form': form})


def request_list(request):
    current_user = _get_current_user(request)
    if not current_user:
        messages.error(request, "Войдите, чтобы посмотреть заявки.")
        return redirect('login')

    queryset = Request.objects.select_related('user_id') \
        .prefetch_related('scrap_types') \
        .exclude(status='completed') \
        .order_by('-total_sum')

    # Ключевая строка: обычный пользователь видит только свои заявки,
    # менеджер — все
    if not _is_manager(current_user):
        queryset = queryset.filter(user_id=current_user)

    total_revenue = queryset.aggregate(total=Sum('total_sum'))['total'] or 0

    paginator = Paginator(queryset, 5)
    page = request.GET.get('page')
    try:
        requests_page = paginator.page(page)
    except PageNotAnInteger:
        requests_page = paginator.page(1)
    except EmptyPage:
        requests_page = paginator.page(paginator.num_pages)

    return render(request, 'requests.html', {
        'requests': requests_page,
        'total_revenue': total_revenue,
        'is_manager': _is_manager(current_user),
    })


def dashboard(request):
    if not request.session.get('user_id'):
        messages.error(request, "Статистика доступна только вошедшим пользователям.")
        return redirect('login')

    # Агрегатные функции
    agg = Request.objects.aggregate(
        total_requests=Count('id'),
        total_revenue=Sum('total_sum'),
        avg_request_sum=Avg('total_sum'),
    )

    # distinct()
    used_statuses = Request.objects.values_list('status', flat=True).distinct()

    # get()
    featured_category = None
    try:
        featured_category = Category.objects.get(title__icontains='чёрный')
    except Category.DoesNotExist:
        pass
    except Category.MultipleObjectsReturned:
        featured_category = Category.objects.filter(title__icontains='чёрный').first()

    # Бизнес-логика: топ клиентов через annotate + Sum по связанным заявкам
    top_clients = User.objects.annotate(total_spent=Sum('requests__total_sum')) \
                      .exclude(total_spent=None) \
                      .order_by('-total_spent')[:5]

    context = {
        'agg': agg,
        'used_statuses': used_statuses,
        'featured_category': featured_category,
        'top_clients': top_clients,
    }
    return render(request, 'dashboard.html', context)


def home(request):
    categories = Category.objects.prefetch_related('scraptype_set').all()

    recent_qs = Request.objects.exclude(status='cancelled').order_by('-created_at')[:6]
    recent_activity = [
        {
            'street': r.address.rsplit(',', 1)[0],
            'status_display': r.get_status_display(),
            'status': r.status,
            'created_at': r.created_at,
        }
        for r in recent_qs
    ]

    stats = {
        'completed_requests': Request.objects.filter(status='completed').count(),
        'scrap_types_count': ScrapType.objects.count(),
        'clients_count': User.objects.filter(role_id__name__icontains='Пользователь').count(),
    }

    current_user = _get_current_user(request)
    search_query = request.GET.get('q', '').strip()
    search_results = None
    if search_query and current_user:
        base_qs = Request.objects.select_related('user_id')
        if not _is_manager(current_user):
            base_qs = base_qs.filter(user_id=current_user)
        search_results = base_qs.filter(address__icontains=search_query)

    context = {
        'categories': categories,
        'recent_activity': recent_activity,
        'stats': stats,
        'search_query': search_query,
        'search_results': search_results,
    }
    return render(request, 'home.html', context)

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


def request_detail(request, pk):
    obj = get_object_or_404(Request, pk=pk)
    current_user = _get_current_user(request)

    if not current_user:
        messages.error(request, "Войдите, чтобы посмотреть заявку.")
        return redirect('login')

    if not _is_manager(current_user) and obj.user_id_id != current_user.id:
        messages.error(request, "У вас нет доступа к этой заявке.")
        return redirect('request_list')

    item_form = RequestItemForm()
    service_form = RequestServiceForm()

    if request.method == 'POST':
        if 'add_item' in request.POST:
            item_form = RequestItemForm(request.POST)
            if item_form.is_valid():
                item = item_form.save(commit=False)
                item.request = obj
                item.save()
                messages.success(request, "Позиция добавлена.")
                return redirect('request_detail', pk=pk)
        elif 'add_service' in request.POST:
            service_form = RequestServiceForm(request.POST)
            if service_form.is_valid():
                service = service_form.save(commit=False)
                service.request_id = obj
                service.save()
                obj.recalculate_total()
                messages.success(request, "Услуга добавлена.")
                return redirect('request_detail', pk=pk)
        elif 'change_status' in request.POST and _is_manager(current_user):
            new_status = request.POST.get('status')
            valid_values = dict(Request.statuses)
            if new_status in valid_values:
                obj.status = new_status
                obj.save()
                messages.success(request, "Статус обновлён.")
            return redirect('request_detail', pk=pk)

    return render(request, 'request_detail.html', {
        'request_obj': obj,
        'item_form': item_form,
        'service_form': service_form,
        'status_choices': Request.statuses,
    })


def request_item_delete(request, pk, item_id):
    current_user = _get_current_user(request)
    if not current_user:
        return redirect('login')

    request_obj = get_object_or_404(Request, pk=pk)
    if not _is_manager(current_user) and request_obj.user_id_id != current_user.id:
        messages.error(request, "У вас нет доступа к этой заявке.")
        return redirect('request_list')

    item = get_object_or_404(RequestItem, pk=item_id, request=request_obj)
    if request.method == 'POST':
        item.delete()
        request_obj.recalculate_total()  # delete() не вызывает save(), пересчитываем вручную
        messages.success(request, "Позиция удалена.")
    return redirect('request_detail', pk=pk)


def request_service_delete(request, pk, service_id):
    current_user = _get_current_user(request)
    if not current_user:
        return redirect('login')

    request_obj = get_object_or_404(Request, pk=pk)
    if not _is_manager(current_user) and request_obj.user_id_id != current_user.id:
        messages.error(request, "У вас нет доступа к этой заявке.")
        return redirect('request_list')

    service = get_object_or_404(Request_services, pk=service_id, request_id=request_obj)
    if request.method == 'POST':
        service.delete()
        request_obj.recalculate_total()
        messages.success(request, "Услуга удалена.")
    return redirect('request_detail', pk=pk)
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
            messages.success(request, "Заявка создана. Теперь добавьте состав лома.")
            return HttpResponseRedirect(reverse('request_detail', args=[new_request.pk]))
    else:
        form = RequestForm()
    return render(request, 'request_form.html', {'form': form, 'action': 'Создать'})


# UPDATE (Редактирование)
def request_edit(request, pk):
    current_user = _get_current_user(request)
    if not current_user:
        return redirect('login')

    request_obj = get_object_or_404(Request, pk=pk)
    if not _is_manager(current_user) and request_obj.user_id_id != current_user.id:
        messages.error(request, "У вас нет доступа к этой заявке.")
        return redirect('request_list')

    if request.method == 'POST':
        form = RequestForm(request.POST, request.FILES, instance=request_obj)
        if form.is_valid():
            form.save()
            return redirect('request_list')
    else:
        form = RequestForm(instance=request_obj)
    return render(request, 'request_form.html', {'form': form, 'action': 'Редактировать'})


# DELETE (Удаление)
def request_delete(request, pk):
    current_user = _get_current_user(request)
    if not current_user:
        return redirect('login')

    request_obj = get_object_or_404(Request, pk=pk)
    if not _is_manager(current_user) and request_obj.user_id_id != current_user.id:
        messages.error(request, "У вас нет доступа к этой заявке.")
        return redirect('request_list')

    if request.method == 'POST':
        request_obj.delete()
        return redirect('request_list')
    return render(request, 'request_confirm_delete.html', {'request_obj': request_obj})
def _get_current_user(request):
    """Возвращает объект User текущей сессии, либо None для гостя."""
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    return User.objects.select_related('role_id').filter(pk=user_id).first()


def _is_manager(user):
    return user is not None and user.role_id and 'менеджер' in user.role_id.name.lower()
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import HttpResponseForbidden, Http404
from django.db.models import Q
from .forms import (
    UserLoginForm,
    IndividualRegistrationForm,
    LegalRegistrationForm,
    IndividualProfileEditForm,
    LegalProfileEditForm,
)
from .models import UserProfile
from shop.models import Order


def login_view(request):
    """Авторизация пользователей (как физлиц, так и юрлиц)."""
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    redirect_to = request.GET.get("next") or request.POST.get("next") or "accounts:profile"

    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            remember_me = form.cleaned_data.get("remember_me", True)
            
            login(request, user)
            
            if not remember_me:
                request.session.set_expiry(0)  # Закрытие сессии при закрытии браузера
            else:
                request.session.set_expiry(1209600)  # 2 недели

            name = user.profile.display_name if hasattr(user, "profile") else user.username
            messages.success(request, f"Добро пожаловать, {name}! Вы успешно авторизованы.")
            return redirect(redirect_to)
    else:
        form = UserLoginForm()

    return render(request, "accounts/login.html", {
        "form": form,
        "next": redirect_to,
    })


def register_view(request):
    """Регистрация новых клиентов: выбор физлицо или юрлицо / ИП."""
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    # Определяем активный тип регистрации (individual или legal)
    account_type = request.GET.get("type", "individual")
    if request.method == "POST":
        account_type = request.POST.get("account_type", account_type)

    indiv_form = IndividualRegistrationForm()
    legal_form = LegalRegistrationForm()

    if request.method == "POST":
        if account_type == "legal":
            legal_form = LegalRegistrationForm(request.POST)
            if legal_form.is_valid():
                user = legal_form.save()
                login(request, user)
                messages.success(
                    request, 
                    f"Организация «{user.profile.company_name}» успешно зарегистрирована! "
                    "Добро пожаловать в B2B личный кабинет «Сибсыр»."
                )
                return redirect("accounts:profile")
        else:
            indiv_form = IndividualRegistrationForm(request.POST)
            if indiv_form.is_valid():
                user = indiv_form.save()
                login(request, user)
                messages.success(
                    request, 
                    f"Здравствуйте, {user.first_name}! Ваш личный кабинет успешно создан. "
                    "Приятных покупок в сыроварне «Сибсыр»!"
                )
                return redirect("accounts:profile")

    return render(request, "accounts/register.html", {
        "account_type": account_type,
        "indiv_form": indiv_form,
        "legal_form": legal_form,
    })


def logout_view(request):
    """Выход из аккаунта."""
    logout(request)
    messages.info(request, "Вы вышли из личного кабинета.")
    return redirect("main:index")


@login_required
def profile_view(request):
    """
    Главная страница Личного кабинета:
    - Обзорная статистика (потрачено, заказов, статус)
    - Реквизиты или профиль покупателя
    - Последние 5 заказов с возможностью перехода
    """
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    orders = profile.get_orders()
    
    total_spent = profile.get_total_spent()
    orders_count = orders.count()
    active_orders = orders.filter(status__in=["new", "processing", "confirmed", "shipped"])
    completed_orders_count = orders.filter(status="completed").count()

    recent_orders = orders[:5]

    return render(request, "accounts/profile.html", {
        "profile": profile,
        "orders_count": orders_count,
        "total_spent": total_spent,
        "active_orders_count": active_orders.count(),
        "completed_orders_count": completed_orders_count,
        "recent_orders": recent_orders,
    })


@login_required
def orders_view(request):
    """
    Полная история всех покупок пользователя:
    - Фильтрация по статусам
    - Подробный состав каждой покупки
    - Прямые ссылки на печать документов (счет, накладная ТОРГ-12, товарный чек)
    """
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    orders_qs = profile.get_orders()

    status_filter = request.GET.get("status", "all")
    if status_filter == "active":
        orders_qs = orders_qs.filter(status__in=["new", "processing", "confirmed", "shipped"])
    elif status_filter == "completed":
        orders_qs = orders_qs.filter(status="completed")
    elif status_filter == "cancelled":
        orders_qs = orders_qs.filter(status="cancelled")

    query = request.GET.get("q", "").strip()
    if query:
        orders_qs = orders_qs.filter(
            Q(id__icontains=query) |
            Q(product_choice__icontains=query) |
            Q(items__title__icontains=query)
        ).distinct()

    orders_list = list(orders_qs)

    return render(request, "accounts/orders.html", {
        "profile": profile,
        "orders": orders_list,
        "status_filter": status_filter,
        "query": query,
        "total_orders_count": profile.get_orders_count(),
    })


@login_required
def order_detail_view(request, order_id):
    """Детальная карточка конкретного заказа с таймлайном и документами."""
    order = get_object_or_404(Order, id=order_id)
    
    # Защита: доступ только владельцу заказа либо сотрудникам
    if not request.user.is_staff and order.user != request.user:
        return HttpResponseForbidden("У вас нет доступа к просмотру этого заказа.")

    items = order.get_order_items()

    return render(request, "accounts/order_detail.html", {
        "order": order,
        "items": items,
        "profile": getattr(request.user, "profile", None),
    })


@login_required
def profile_edit_view(request):
    """Редактирование профиля и реквизитов организации/покупателя."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if profile.is_legal:
        form_class = LegalProfileEditForm
    else:
        form_class = IndividualProfileEditForm

    if request.method == "POST":
        form = form_class(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Данные вашего профиля успешно обновлены!")
            return redirect("accounts:profile")
    else:
        form = form_class(request.user)

    return render(request, "accounts/profile_edit.html", {
        "form": form,
        "profile": profile,
    })


@login_required
def password_change_view(request):
    """Смена пароля аккаунта."""
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Не разлогинивать пользователя
            messages.success(request, "Ваш пароль был успешно изменен!")
            return redirect("accounts:profile")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "accounts/password_change.html", {
        "form": form,
    })

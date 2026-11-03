import json
from decimal import Decimal
from django.contrib import admin
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from functools import wraps

from django.contrib.auth.models import User, Group
from accounts.models import UserProfile
from shop.models import Product, Category, Order, OrderItem, Review, Promotion, PromoCode
from main.models import (
    SiteSettings, CallbackRequest, ProductionFeature, CompanyTimeline,
    QualityCertificate, DeliveryMethod, PaymentMethod, DeliveryFaq,
    ContactDepartment, FaqCategory, FaqItem, SocialLink, WholesalePriceRequest
)
from articles.models import Article


def get_admin_nav_counts():
    """Сводные счетчики для глобального меню админки (новые заказы, заявки и т.д.)"""
    try:
        new_orders = Order.objects.filter(status='new').count()
        pending_callbacks = CallbackRequest.objects.filter(is_processed=False).count()
        pending_wholesale = WholesalePriceRequest.objects.filter(approval_status='pending').count()
        total_alerts = new_orders + pending_callbacks + pending_wholesale
        return {
            'new_orders': new_orders,
            'pending_callbacks': pending_callbacks,
            'pending_wholesale': pending_wholesale,
            'total_alerts': total_alerts,
        }
    except Exception:
        return {
            'new_orders': 0,
            'pending_callbacks': 0,
            'pending_wholesale': 0,
            'total_alerts': 0,
        }


def get_dashboard_statistics():
    """Собирает полную аналитику и статистические данные для главной страницы админки."""
    now = timezone.now()
    
    # 1. Заказы и выручка
    orders_qs = Order.objects.all()
    total_orders = orders_qs.count()
    
    total_revenue = orders_qs.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
    paid_revenue = orders_qs.filter(is_paid=True).aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
    pending_revenue = orders_qs.filter(is_paid=False).aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
    
    avg_order_value = (total_revenue / total_orders) if total_orders > 0 else Decimal('0.00')
    
    new_orders_count = orders_qs.filter(status='new').count()
    processing_orders_count = orders_qs.filter(status='processing').count()
    completed_orders_count = orders_qs.filter(status='completed').count()
    cancelled_orders_count = orders_qs.filter(status='cancelled').count()
    
    legal_orders_count = orders_qs.filter(customer_type='legal').count()
    individual_orders_count = orders_qs.filter(customer_type='individual').count()
    
    # 2. Каталог продукции
    products_qs = Product.objects.all()
    total_products = products_qs.count()
    active_products = products_qs.filter(is_active=True).count()
    inactive_products = products_qs.filter(is_active=False).count()
    featured_products = products_qs.filter(is_featured=True).count()
    
    categories_qs = Category.objects.annotate(prod_count=Count('products')).order_by('-prod_count')
    total_categories = categories_qs.count()
    
    category_names = []
    category_counts = []
    for cat in categories_qs:
        if cat.prod_count > 0:
            category_names.append(cat.name)
            category_counts.append(cat.prod_count)
            
    # Если в категориях пусто или мало, берем топ
    chart_category_labels = category_names[:8]
    chart_category_data = category_counts[:8]
    
    # 3. Заявки и обращения
    callbacks_qs = CallbackRequest.objects.all()
    total_callbacks = callbacks_qs.count()
    pending_callbacks = callbacks_qs.filter(is_processed=False).count()
    processed_callbacks = callbacks_qs.filter(is_processed=True).count()
    pending_wholesale_requests = callbacks_qs.filter(request_type='wholesale', approval_status='pending').count()
    
    # 4. Отзывы
    reviews_qs = Review.objects.all()
    total_reviews = reviews_qs.count()
    avg_rating = reviews_qs.aggregate(avg=Avg('rating'))['avg']
    avg_rating = round(avg_rating, 1) if avg_rating else 5.0
    pending_reviews = reviews_qs.filter(is_approved=False).count()
    
    # 5. Статьи и контент
    articles_qs = Article.objects.all()
    total_articles = articles_qs.count()
    published_articles = articles_qs.filter(is_published=True).count()
    total_article_views = articles_qs.aggregate(v=Sum('views_count'))['v'] or 0
    
    # 6. Свежие записи для быстрого доступа
    recent_orders = orders_qs.select_related().order_by('-created_at')[:7]
    recent_callbacks = callbacks_qs.order_by('-created_at')[:5]
    recent_reviews = reviews_qs.order_by('-created_at')[:4]
    top_featured_products = products_qs.filter(is_featured=True).select_related('category')[:6]
    
    # 7. Данные для графиков Chart.js
    order_statuses_data = {
        'labels': ['Новые', 'В обработке', 'Подтвержденные/Отгруженные', 'Выполненные', 'Отмененные'],
        'counts': [
            orders_qs.filter(status='new').count(),
            orders_qs.filter(status='processing').count(),
            orders_qs.filter(status__in=['confirmed', 'shipped']).count(),
            orders_qs.filter(status='completed').count(),
            orders_qs.filter(status='cancelled').count(),
        ]
    }
    
    customer_types_data = {
        'labels': ['Физлица (Розница)', 'Юрлица и ИП (Опт/B2B)'],
        'counts': [individual_orders_count, legal_orders_count]
    }
    
    site_settings = SiteSettings.get_solo()
    
    return {
        'stats': {
            'total_revenue': total_revenue,
            'paid_revenue': paid_revenue,
            'pending_revenue': pending_revenue,
            'avg_order_value': avg_order_value,
            'total_orders': total_orders,
            'new_orders_count': new_orders_count,
            'processing_orders_count': processing_orders_count,
            'completed_orders_count': completed_orders_count,
            'cancelled_orders_count': cancelled_orders_count,
            'legal_orders_count': legal_orders_count,
            'individual_orders_count': individual_orders_count,
            'total_products': total_products,
            'active_products': active_products,
            'inactive_products': inactive_products,
            'featured_products': featured_products,
            'total_categories': total_categories,
            'total_callbacks': total_callbacks,
            'pending_callbacks': pending_callbacks,
            'processed_callbacks': processed_callbacks,
            'pending_wholesale_requests': pending_wholesale_requests,
            'total_reviews': total_reviews,
            'avg_rating': avg_rating,
            'pending_reviews': pending_reviews,
            'total_articles': total_articles,
            'published_articles': published_articles,
            'total_article_views': total_article_views,
            'total_promotions': Promotion.objects.count(),
            'active_promotions': Promotion.objects.filter(is_active=True).count(),
            'total_promocodes': PromoCode.objects.count(),
            'active_promocodes': PromoCode.objects.filter(is_active=True).count(),
            'total_wholesale_requests': WholesalePriceRequest.objects.count(),
            'total_users': User.objects.count(),
            'total_profiles': UserProfile.objects.count(),
            'total_groups': Group.objects.count(),
            'total_features': ProductionFeature.objects.count(),
            'total_timeline': CompanyTimeline.objects.count(),
            'total_certificates': QualityCertificate.objects.count(),
            'total_delivery_methods': DeliveryMethod.objects.count(),
            'total_payment_methods': PaymentMethod.objects.count(),
            'total_departments': ContactDepartment.objects.count(),
            'total_faqs': FaqItem.objects.count(),
            'total_socials': SocialLink.objects.count(),
        },
        'categories_list': categories_qs[:8],
        'recent_orders': recent_orders,
        'recent_callbacks': recent_callbacks,
        'recent_reviews': recent_reviews,
        'top_featured_products': top_featured_products,
        'site_settings_obj': site_settings,
        'chart_categories_json': json.dumps({
            'labels': chart_category_labels,
            'data': chart_category_data,
        }, ensure_ascii=False),
        'chart_statuses_json': json.dumps(order_statuses_data, ensure_ascii=False),
        'chart_customers_json': json.dumps(customer_types_data, ensure_ascii=False),
    }


def get_accounts_dashboard_statistics():
    """Собирает аналитику по клиентам и учетным записям для /admin/accounts/."""
    from django.contrib.auth import get_user_model
    from accounts.models import UserProfile
    from shop.models import Order
    User = get_user_model()
    
    users_qs = User.objects.all()
    profiles_qs = UserProfile.objects.all()
    
    total_users = users_qs.count()
    total_profiles = profiles_qs.count()
    legal_count = profiles_qs.filter(customer_type='legal').count()
    individual_count = profiles_qs.filter(customer_type='individual').count()
    staff_count = users_qs.filter(is_staff=True).count()
    
    registered_orders = Order.objects.filter(user__isnull=False)
    registered_orders_count = registered_orders.count()
    registered_orders_sum = registered_orders.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
    
    active_buyers_count = registered_orders.values_list('user_id', flat=True).distinct().count()
    
    recent_profiles = list(profiles_qs.select_related('user').order_by('-created_at')[:15])
    
    return {
        'accounts_stats': {
            'total_users': total_users,
            'total_profiles': total_profiles,
            'legal_count': legal_count,
            'individual_count': individual_count,
            'staff_count': staff_count,
            'active_buyers_count': active_buyers_count,
            'registered_orders_count': registered_orders_count,
            'registered_orders_sum': registered_orders_sum,
        },
        'recent_accounts': recent_profiles,
    }


def patch_admin_site():
    """Подключает дашборд с расширенной аналитикой к стандартной админке Django."""
    if getattr(admin.site, '_dashboard_patched', False):
        return

    original_index = admin.site.index
    original_app_index = admin.site.app_index
    original_each_context = admin.site.each_context

    @wraps(original_each_context)
    def custom_admin_each_context(request):
        ctx = original_each_context(request)
        ctx['admin_nav_counts'] = get_admin_nav_counts()
        return ctx

    @wraps(original_index)
    def custom_admin_index(request, extra_context=None):
        try:
            dashboard_context = get_dashboard_statistics()
        except Exception as e:
            dashboard_context = {'dashboard_error': str(e)}

        extra_context = {**(extra_context or {}), **dashboard_context}
        return original_index(request, extra_context=extra_context)

    @wraps(original_app_index)
    def custom_admin_app_index(request, app_label, extra_context=None):
        app_context = {}
        if app_label == 'accounts':
            try:
                app_context = get_accounts_dashboard_statistics()
            except Exception as e:
                app_context = {'accounts_error': str(e)}
        extra_context = {**(extra_context or {}), **app_context}
        return original_app_index(request, app_label, extra_context=extra_context)

    admin.site.index = custom_admin_index
    admin.site.app_index = custom_admin_app_index
    admin.site.each_context = custom_admin_each_context
    admin.site._dashboard_patched = True


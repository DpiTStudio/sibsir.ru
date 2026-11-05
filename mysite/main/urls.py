from django.urls import path
from . import views
from . import admin_backup_views

app_name = 'main'

urlpatterns = [
    # Управление резервными копиями и деплоем (только суперпользователи)
    path('admin-backups/', admin_backup_views.admin_backup_dashboard, name='admin_backup_dashboard'),
    path('admin-backups/create/', admin_backup_views.admin_backup_create, name='admin_backup_create'),
    path('admin-backups/download/<str:filename>/', admin_backup_views.admin_backup_download, name='admin_backup_download'),
    path('admin-backups/restore/', admin_backup_views.admin_backup_restore, name='admin_backup_restore'),
    path('admin-backups/delete/<str:filename>/', admin_backup_views.admin_backup_delete, name='admin_backup_delete'),

    path('', views.index, name='index'),
    path('catalog/', views.catalog_view, name='catalog'),
    path('categories/', views.categories_list_view, name='categories'),
    path('catalog/categories/', views.categories_list_view, name='catalog_categories'),
    path('catalog/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('product/<slug:slug>/', views.product_detail_view, name='product_detail_alias'),
    path('about/', views.about_view, name='about'),
    path('delivery/', views.delivery_view, name='delivery'),
    path('reviews/', views.reviews_view, name='reviews'),
    path('reviews/create/', views.create_review, name='create_review'),
    path('contacts/', views.contacts_view, name='contacts'),
    path('faq/', views.faq_view, name='faq'),
    path('company/faq/', views.faq_view, name='company_faq'),
    # Страницы компании и регламентные документы (/company/consent/, /company/soglasie/)
    path('company/consent/', views.company_page_detail_view, {'slug': 'consent'}, name='company_consent'),
    path('company/soglasie/', views.company_page_detail_view, {'slug': 'soglasie'}, name='company_soglasie'),
    path('company/<slug:slug>/', views.company_page_detail_view, name='company_page_detail'),
    path('articles/', views.articles_list_view, name='articles'),
    path('articles/<slug:slug>/', views.article_detail_view, name='article_detail'),
    path('search/', views.search_view, name='search'),
    path('api/search/', views.search_api, name='search_api'),
    path('order/create/', views.create_order, name='create_order'),
    path('callback/create/', views.create_callback, name='create_callback'),
    path('captcha/refresh/', views.captcha_refresh, name='captcha_refresh'),
    path('api/article/<slug:slug>/', views.get_article_detail, name='article_detail_api'),
    path('article/<slug:slug>/', views.get_article_detail, name='legacy_article_detail_api'),
    # Динамические контентные и посадочные страницы (SEO)
    path('pages/<slug:slug>/', views.page_detail_view, name='page_detail'),
    path('<slug:slug>/', views.page_detail_view, name='page_direct'),
]

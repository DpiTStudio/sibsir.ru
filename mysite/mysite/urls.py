"""
URL configuration for mysite project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from main.views import tinymce_image_upload
from main.seo_views import robots_txt_view, sitemap_xml_view, favicon_view

urlpatterns = [
    path('favicon.ico', favicon_view, name='favicon'),
    path('robots.txt', robots_txt_view, name='robots_txt'),
    path('sitemap.xml', sitemap_xml_view, name='sitemap_xml'),
    path('admin/', admin.site.urls),
    path('tinymce/', include('tinymce.urls')),
    path('admin-tinymce-upload/', tinymce_image_upload, name='tinymce_image_upload'),
    path('shop/', include('shop.urls')),
    path('accounts/', include('accounts.urls')),
    path('', include('main.urls')),
]

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    if hasattr(settings, 'MEDIA_ROOT'):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

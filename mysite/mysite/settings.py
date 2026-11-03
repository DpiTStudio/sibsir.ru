"""
Настройки Django для проекта mysite.
Создано «django-admin startproject» с использованием Django 5.2.17.
Дополнительную информацию об этом файле см.
https://docs.djangoproject.com/en/5.2/topics/settings/
Полный список настроек и их значений см.
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

# импорт
import os
from pathlib import Path

# Создайте пути внутри проекта следующим образом: BASE_DIR/'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Настройки быстрого запуска разработки - непригодны для производства
# См. https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/.

# ПРЕДУПРЕЖДЕНИЕ О БЕЗОПАСНОСТИ: храните секретный ключ, используемый в производстве, в тайне!
SECRET_KEY = "django-insecure-11s9&btbcgshl#_6&*fe2*=$^tkm=75m43(n^z^*$oiu&wlxmr"

# ПРЕДУПРЕЖДЕНИЕ БЕЗОПАСНОСТИ: не запускайте с включенной отладкой в ​​рабочей среде!
DEBUG = True

# Разрешенные хосты (только доменные имена и IP-адреса, без http:// и без портов)
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "sibsir.ru",
    "www.sibsir.ru",
]

# Доверенные источники для защиты CSRF (с указанием протокола http/https и портов)
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8880",
    "http://localhost:8880",
    "https://sibsir.ru",
    "https://www.sibsir.ru",
]



# Определение приложения

INSTALLED_APPS = [
    # встроенные приложения django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # пользовательские приложения
    "main.apps.MainConfig",
    "shop.apps.ShopConfig",
    "articles.apps.ArticlesConfig",
    "accounts.apps.AccountsConfig",
    # Сторонние приложения
    "tinymce",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Главный маршрут
ROOT_URLCONF = "mysite.urls"


# Шаблоны
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "main.context_processors.site_settings",
            ],
        },
    },
]

# WSGI приложение
WSGI_APPLICATION = "mysite.wsgi.application"


# База данных
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Проверка пароля
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Интернационализация
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True


# Статические файлы (CSS, JavaScript, изображения)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = "/static/"

# Папки со статическими файлами проекта (исходники стилей, скриптов и изображений проекта)
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Папка, куда команда `collectstatic` собирает ВСЮ статику для продакшена (включая админку).
# ВАЖНО: не должна совпадать со STATICFILES_DIRS!
STATIC_ROOT = BASE_DIR / "staticfiles"

# Хранилища файлов по умолчанию (новый формат Django 4.2+ / 5.x вместо устаревшего STATICFILES_STORAGE)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


# Медиафайлы (файлы, загружаемые пользователями и администратором через модели)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Тип поля первичного ключа по умолчанию
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Настройки авторизации и личного кабинета
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:profile"
LOGOUT_REDIRECT_URL = "main:index"

# Настройки визуального редактора TinyMCE
TINYMCE_DEFAULT_CONFIG = {
    "theme": "silver",
    "skin": "oxide-dark",
    "content_css": "dark",
    "height": 420,
    "menubar": "file edit view insert format tools table",
    "browser_spellcheck": True,
    "language": "ru",
    "plugins": (
        "advlist autolink lists link image media table code codesample "
        "wordcount visualblocks fullscreen searchreplace directionality charmap preview"
    ),
    "toolbar": (
        "undo redo | blocks fontfamily fontsize | bold italic underline strikethrough | "
        "forecolor backcolor | alignleft aligncenter alignright alignjustify | "
        "bullist numlist outdent indent | link image media table | "
        "removeformat code fullscreen"
    ),
    "image_advtab": True,
    "automatic_uploads": True,
    "images_upload_url": "/admin-tinymce-upload/",
    "paste_data_images": True,
    "branding": False,
    "promotion": False,
    "relative_urls": False,
    "remove_script_host": False,
    "convert_urls": True,
    "content_style": """
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 15px;
            line-height: 1.65;
            color: #f1f5f9;
            background-color: #151d30;
            padding: 14px 16px;
        }
        h1, h2, h3, h4, h5, h6 { color: #ffffff; font-weight: 700; margin-top: 1.2em; margin-bottom: 0.5em; }
        p { margin-bottom: 0.85em; color: #e2e8f0; }
        table { border-collapse: collapse; width: 100%; margin: 16px 0; }
        th, td { border: 1px solid #334155; padding: 8px 12px; }
        th { background: #1e293b; font-weight: 600; color: #f8fafc; }
        blockquote { border-left: 4px solid #ff8400; padding: 10px 14px; margin: 16px 0; color: #cbd5e1; font-style: italic; background: rgba(255, 132, 0, 0.1); border-radius: 0 8px 8px 0; }
        img { max-width: 100%; height: auto; border-radius: 8px; }
        a { color: #ff8400; text-decoration: underline; }
        ul, ol { padding-left: 24px; margin-bottom: 1em; color: #e2e8f0; }
        li { margin-bottom: 0.25em; }
        code { background: #1e293b; color: #f59e0b; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
    """,
}


# ==========================================
# Email Configuration (Оптовые рассылки и уведомления)
# ==========================================
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.yandex.ru")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 465))
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "True").lower() in ("true", "1")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "False").lower() in ("true", "1")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "sibs@list.ru")

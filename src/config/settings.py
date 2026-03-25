import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

def env_flag(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


DEBUG = env_flag("DEBUG", default=False)

_secret_key = os.getenv("SECRET_KEY")
if not _secret_key:
    raise ImproperlyConfigured(
        "SECRET_KEY ortam değişkeni tanımlanmamış. "
        "Sunucuyu başlatmadan önce uzun ve rastgele bir değer atayın."
    )
SECRET_KEY = _secret_key

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "127.0.0.1,localhost")
railway_hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if railway_hostname and railway_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(railway_hostname)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_ratelimit',
    'core',
    'dashboard',
    'library',
    'notifications',
    'support',
    'users',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [PROJECT_ROOT / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.notification_summary',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    DATABASES["default"] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'tr-tr'

TIME_ZONE = 'Europe/Istanbul'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [PROJECT_ROOT / 'static']
STATIC_ROOT = PROJECT_ROOT / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", PROJECT_ROOT / 'media'))

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

AUTH_USER_MODEL = 'users.User'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard:home'
LOGOUT_REDIRECT_URL = 'home'

PASSWORD_RESET_TIMEOUT = 3600  # 1 saat

# --- E-posta ---
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = env_flag('EMAIL_USE_TLS', default=True)
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
    SERVER_EMAIL = DEFAULT_FROM_EMAIL

# --- Dosya yükleme limitleri ---
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 MB — bu boyutun üstü temp diske yazılır
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # POST body limiti

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TEST_RUNNER = 'config.test_runner.AuraTestRunner'

# --- Cache (rate limiting için zorunlu) ---
# LocMemCache: her gunicorn worker kendi bellek cache'ini tutar.
# Atomik sayaç desteği olmadığı için django-ratelimit'in strict kontrolü
# uyarı verir; ancak küçük ölçekli (2 worker) dağıtımda limit değerleri
# worker başına uygulandığından pratikte etkili koruma sağlar.
# İleride Redis eklentisi kurulursa CACHES buradan kolayca güncellenebilir.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "aura-ratelimit",
    }
}

# django-ratelimit, LocMemCache'in paylaşımlı olmadığı konusunda sistem check
# hatası fırlatır. Bu mimari bilinçli bir tercih; gelecekte Redis ile değiştirilebilir.
SILENCED_SYSTEM_CHECKS = ["django_ratelimit.E003", "django_ratelimit.W001"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    SECURE_SSL_REDIRECT = env_flag("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_flag(
        "SECURE_HSTS_INCLUDE_SUBDOMAINS",
        True,
    )
    SECURE_HSTS_PRELOAD = env_flag("SECURE_HSTS_PRELOAD", True)
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'

# --- Loglama ---
# Railway stdout/stderr'i otomatik yakalar; dosya handler'a gerek yok.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "WARNING"),
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "support": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "notifications": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

"""
Django settings for mikosite project.

Generated by 'django-admin startproject' using Django 5.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from .secrets import SECRET_KEY, DB_PASSWORD
except ImportError:
    raise ImportError("Create a secrets.py file with SECRET_KEY and DB_PASSWORD")

CSRF_TRUSTED_ORIGINS = [
    'https://mikomath.org',
    'http://mikomath.org',
    "https://195.117.15.149",
    "http://195.117.15.149",
]

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 1209600  # 2 weeks, in seconds
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']

ALLOWED_HOSTS = [
    "mikomath.org",
    "195.117.15.149",
    "127.0.0.1",
    "localhost",
]

APPEND_SLASH = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'compressor',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'more_admin_filters',
    'rangefilter',
    "accounts",
    "mainSite",
    "hintBase",
    "taggit",
    "formtools",
    "seminars",
    "cards",
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',  # For browser-based access
        'rest_framework.authentication.TokenAuthentication',    # For API access with tokens
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'mikosite.permissions.IsAdminUserOrReadOnly',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'mikosite.throttling.SessionUserThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'session_user': '1440/day',
    },
    'DEFAULT_PAGINATION_CLASS': 'mikosite.pagination.CustomLimitOffsetPagination',
    'PAGE_SIZE': 30,
}

USE_L10N = True
TAGGIT_CASE_INSENSITIVE = True

TEMPLATES = [
    {
        'NAME': 'tex',
        'BACKEND': 'django_tex.engine.TeXEngine',
        'APP_DIRS': True,
    },
]

MIDDLEWARE = [
    # 'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mikosite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mikosite.wsgi.application'

sqlite_db_path = BASE_DIR / 'db.sqlite3'

if sqlite_db_path.exists():
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': sqlite_db_path,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'mikodb',
            'USER': 'postgres',
            'PASSWORD': DB_PASSWORD,
            'HOST': 'localhost',
            'PORT': '5432',
            'OPTIONS': {
                'pool': {
                    'min_size': 2,
                    'max_size': 4,
                    'timeout': 10,
                }
            }
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
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

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
CACHE_BACKEND = 'redis_cache.cache://127.0.0.1:6379/1'
SESSION_CACHE_ALIAS = "default"
# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'pl-pl'

TIME_ZONE = 'Europe/Warsaw'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)
COMPRESS_OFFLINE = True

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = "accounts.User"

"""
Django settings for gram_panchayat project.
"""

from pathlib import Path
from decouple import config
from django.core.exceptions import ImproperlyConfigured
import os
import pymysql
import dj_database_url
from django.utils.translation import gettext_lazy as _

# Use PyMySQL as MySQLdb
pymysql.install_as_MySQLdb()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'https://*.loca.lt',
    'https://*.lhr.life',
    'https://*.pinggy.link',
    'https://*.ngrok-free.app',
    'https://*.onrender.com',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'portal_app',
    'crispy_forms',
    'crispy_bootstrap5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'portal_app.middleware.RoleBasedAccessMiddleware',  # Role-based access control
]

ROOT_URLCONF = 'gram_panchayat.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'portal_app.context_processors.ui_badges',
            ],
        },
    },
]

WSGI_APPLICATION = 'gram_panchayat.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASE_URL = config('DATABASE_URL', default=None)
IS_VERCEL = config('VERCEL', default=False, cast=bool) or 'VERCEL' in os.environ

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    }
else:
    DB_ENGINE = config('DB_ENGINE', default='sqlite' if IS_VERCEL else 'mysql')

    if DB_ENGINE == 'sqlite' or IS_VERCEL:
        import shutil
        tmp_db = Path('/tmp/db.sqlite3')
        orig_db = BASE_DIR / 'db.sqlite3'
        if IS_VERCEL and orig_db.exists() and not tmp_db.exists():
            try:
                shutil.copy2(orig_db, tmp_db)
            except Exception:
                pass
        db_path = tmp_db if (IS_VERCEL and tmp_db.exists()) else orig_db
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': db_path,
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': config('DB_NAME', default='gram_panchayat_db'),
                'USER': config('DB_USER', default='root'),
                'PASSWORD': config('DB_PASSWORD', default=''),
                'HOST': config('DB_HOST', default='localhost'),
                'PORT': config('DB_PORT', default='3306'),
                'OPTIONS': {
                    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                    'charset': 'utf8mb4',
                },
            }
        }

# Custom User Model
AUTH_USER_MODEL = 'portal_app.CustomUser'

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', _('English')),
    ('hi', _('Hindi')),
    ('mr', _('Marathi')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (User uploaded files)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Login Settings
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'

# Session Security Settings
SESSION_COOKIE_AGE = 3600  # 1 hour (3600 seconds)
SESSION_SAVE_EVERY_REQUEST = True  # Extend session on each request
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Session expires when browser closes
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_COOKIE_NAME = 'gram_panchayat_sessionid'  # Custom session cookie name
LANGUAGE_COOKIE_NAME = 'gram_panchayat_language'
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365
LANGUAGE_COOKIE_SAMESITE = 'Lax'

# CSRF Protection
CSRF_COOKIE_HTTPONLY = True  # Prevent JavaScript access to CSRF cookie
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_NAME = 'gram_panchayat_csrftoken'

# Password Strength
# Using Django's default PBKDF2 hasher (reliable and secure)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',  # Django default (secure & stable)
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# Security Settings (Production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    # Development settings
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# Site Configuration
SITE_NAME = "Digital Gram Panchayat Portal"
PANCHAYAT_NAME = "Model Gram Panchayat"
PROJECT_NAME = "Digital Gram Panchayat Portal"


# ============================================
# CHATBOT CONFIGURATION
# ============================================

CHATBOT_ENABLED = config('CHATBOT_ENABLED', default=True, cast=bool)
CHATBOT_PROVIDER = config('CHATBOT_PROVIDER', default='openai').strip().lower()
CHATBOT_TIMEOUT_SECONDS = config('CHATBOT_TIMEOUT_SECONDS', default=8, cast=int)
CHATBOT_HISTORY_LIMIT = config('CHATBOT_HISTORY_LIMIT', default=8, cast=int)
CHATBOT_OPENAI_API_KEY = config('OPENAI_API_KEY', default='').strip()
CHATBOT_OPENAI_MODEL = config('OPENAI_MODEL', default='gpt-4o-mini').strip()
CHATBOT_GEMINI_API_KEY = config('GEMINI_API_KEY', default='').strip()
CHATBOT_GEMINI_MODEL = config('GEMINI_MODEL', default='gemini-1.5-flash').strip()


# ============================================
# EMAIL CONFIGURATION (OTP Verification)
# ============================================

# Email Backend
# For development: Console backend (prints emails to console)
# For production: SMTP backend (sends actual emails)

# Allow explicit override from .env; default uses console in DEBUG and SMTP otherwise
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend'
)

# SMTP Configuration (for production)
# Configure these in .env file for security
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@grampanchayat.gov.in')
EMAIL_FROM_NAME = config('EMAIL_FROM_NAME', default='Digital Grampanchayat Portal')

# Email Settings
EMAIL_TIMEOUT = 10  # seconds
EMAIL_SUBJECT_PREFIX = '[Gram Panchayat] '

# OTP Configuration
OTP_EXPIRY_MINUTES = 10  # OTP expires after 10 minutes
OTP_MAX_ATTEMPTS = 3     # Maximum verification attempts per OTP
OTP_LENGTH = 6           # 6-digit OTP

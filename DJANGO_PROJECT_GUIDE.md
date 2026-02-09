# 🏗️ Django Project Creation & Structure Guide

## 1. CREATING A DJANGO PROJECT

### **1.1 What is `django-admin startproject`?**

`django-admin startproject` is Django's command to scaffold (create the initial structure of) a brand new project with all necessary configuration files.

#### **Command Syntax**
```bash
django-admin startproject project_name [directory]
```

#### **Our Example**
```bash
django-admin startproject grampanchayat
```

This creates the following structure:

```
grampanchayat/                          # ← Outer directory (project container)
├── manage.py                           # ← Management script
└── grampanchayat/                      # ← Inner directory (configuration package)
    ├── __init__.py                     # ← Python package marker
    ├── settings.py                     # ← Project settings
    ├── urls.py                         # ← URL routing
    ├── asgi.py                         # ← ASGI config (for production servers)
    └── wsgi.py                         # ← WSGI config (for production servers)
```

### **1.2 Project Structure Breakdown**

```
grampanchayat/
│
├── manage.py                           # Main Django management command
│   └── Used for: runserver, migrate, createsuperuser, etc.
│
└── grampanchayat/                      # Project configuration package
    ├── __init__.py                     # Makes this a Python package
    ├── settings.py                     # All project settings (database, apps, etc.)
    ├── urls.py                         # Root URL configuration
    ├── asgi.py                         # ASGI application (modern async web servers)
    └── wsgi.py                         # WSGI application (traditional web servers)
```

---

## 2. MANAGE.PY - THE CONTROL CENTER

### **2.1 What is `manage.py`?**

`manage.py` is a Python script that acts as Django's command-line interface for your project. It's essentially a wrapper around `django-admin` that automatically sets your project settings.

**Key Difference:**
```bash
django-admin startproject      # Used to CREATE new projects (no project context)
python manage.py command       # Used to MANAGE existing projects (knows your settings)
```

### **2.2 Common manage.py Commands**

#### **Development Commands**

```bash
# Start development server
python manage.py runserver
python manage.py runserver 8001          # Run on different port
python manage.py runserver 0.0.0.0:8000  # Make accessible from network

# Create database tables
python manage.py migrate

# Create new migrations
python manage.py makemigrations
python manage.py makemigrations app_name

# Create admin superuser
python manage.py createsuperuser

# Interactive Python shell with Django context
python manage.py shell
```

#### **Database Commands**

```bash
# Show SQL for migrations without running them
python manage.py sqlmigrate app_name 0001

# Check database integrity
python manage.py check

# Load data from fixtures
python manage.py loaddata fixture_name

# Dump data to JSON/YAML
python manage.py dumpdata app_name > data.json
```

#### **App Management Commands**

```bash
# Create new Django app
python manage.py startapp app_name

# Run tests
python manage.py test
python manage.py test app_name.tests.TestClassName

# Collect static files (CSS, JS, images for production)
python manage.py collectstatic
```

#### **Utility Commands**

```bash
# Clear sessions
python manage.py clearsessions

# Flush (delete all data from database)
python manage.py flush

# Remove unused migrations
python manage.py squashmigrations app_name

# Show all available commands
python manage.py help
```

### **2.3 manage.py Source Code**

```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    # Sets the DJANGO_SETTINGS_MODULE environment variable
    # This tells Django which settings file to use
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grampanchayat.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Execute whatever command was passed
    # e.g., if you run "python manage.py runserver"
    # sys.argv = ['manage.py', 'runserver']
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
```

**Key Point:** Line 9 shows that `manage.py` automatically points Django to your project's `settings.py` file. This is why you don't need to specify the settings file every time.

---

## 3. DJANGO PROJECT STRUCTURE IN DETAIL

### **3.1 Complete Project Organization**

A complete Django project typically looks like this:

```
grampanchayat/                          # Project root directory
│
├── manage.py                           # Management script
│
├── db.sqlite3                          # SQLite database (development)
│
├── grampanchayat/                      # Configuration package
│   ├── __init__.py
│   ├── settings.py                     # ⭐ Main settings file
│   ├── urls.py                         # ⭐ URL routing
│   ├── asgi.py
│   └── wsgi.py
│
├── portal_app/                         # First Django app
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py
│   ├── __init__.py
│   ├── admin.py                        # Register models in admin
│   ├── apps.py                         # App configuration
│   ├── models.py                       # Database models
│   ├── tests.py                        # Unit tests
│   ├── views.py                        # View functions/classes
│   └── urls.py                         # App-specific URL routing
│
├── templates/                          # HTML templates
│   └── portal_app/
│       ├── base.html
│       ├── home.html
│       └── ...
│
├── static/                             # Static files
│   ├── css/
│   ├── js/
│   └── images/
│
├── media/                              # User-uploaded files
│   └── uploads/
│
├── requirements.txt                    # Python dependencies
├── README.md                           # Project documentation
└── .env                                # Environment variables (secrets)
```

### **3.2 Key Directories Explained**

| Directory | Purpose | Examples |
|-----------|---------|----------|
| `grampanchayat/` (inner) | Project configuration package | settings, urls, wsgi |
| `portal_app/` | Django application (reusable component) | models, views, forms |
| `migrations/` | Database schema change history | 0001_initial.py, 0002_add_field.py |
| `templates/` | HTML files for rendering pages | base.html, home.html |
| `static/` | CSS, JavaScript, images (never change) | bootstrap.css, main.js |
| `media/` | User uploads (change frequently) | profile_photos/, certificates/ |

---

## 4. SETTINGS.PY - THE BRAIN OF YOUR PROJECT

### **4.1 What is settings.py?**

`settings.py` contains all configuration for your Django project. It controls:
- Database connection
- Installed apps
- Middleware
- Templates
- Static files
- Security settings
- And much more!

### **4.2 Essential Settings Explained**

#### **A. BASE_DIR - Project Root Path**
```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
```
- `__file__` = path to settings.py
- `.resolve()` = convert to absolute path
- `.parent` (once) = grampanchayat/ folder
- `.parent` (twice) = grampanchayat/ root folder
- Used for building other paths dynamically

#### **B. SECRET_KEY - Security Token**
```python
SECRET_KEY = 'django-insecure-$wfc!_t$zwr^tlm&7zx3n&0r&0%_=4thxyn545%z)$7$xk02$5'
```
- Used to sign cookies, CSRF tokens, password reset tokens
- ⚠️ **NEVER commit to git in production!**
- Generate new one using:
  ```python
  from django.core.management.utils import get_random_secret_key
  print(get_random_secret_key())
  ```

#### **C. DEBUG - Development Mode**
```python
DEBUG = True
```
- `True` = Show detailed error pages (development)
- `False` = Show generic error pages (production)
- ⚠️ **MUST be False in production!**

#### **D. ALLOWED_HOSTS - Trusted Domains**
```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'yourdomain.com']
```
- Controls which domains can access your app
- `['*']` = Accept all (not recommended)

#### **E. INSTALLED_APPS - Active Modules**
```python
INSTALLED_APPS = [
    'django.contrib.admin',           # Admin interface
    'django.contrib.auth',            # User authentication
    'django.contrib.contenttypes',    # Content type framework
    'django.contrib.sessions',        # Session management
    'django.contrib.messages',        # Message framework
    'django.contrib.staticfiles',     # Static file serving
    'portal_app',                     # Your custom app
    'crispy_forms',                   # Third-party package
]
```
- Each entry represents a Django app or third-party package
- Order matters for some apps
- Must add your apps here after creating them

#### **F. MIDDLEWARE - Request Processing Pipeline**
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',           # Security headers
    'django.contrib.sessions.middleware.SessionMiddleware',    # User sessions
    'django.middleware.common.CommonMiddleware',               # Common utilities
    'django.middleware.csrf.CsrfViewMiddleware',               # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware', # User authentication
    'django.contrib.messages.middleware.MessageMiddleware',    # Messages system
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Clickjacking protection
]
```
- Processes every request and response
- Order is important (top to bottom)
- Acts like layers of a filter

#### **G. TEMPLATES - HTML Rendering**
```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],         # Where Django looks for templates
        'APP_DIRS': True,                         # Look in each app's templates/
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```
- Tells Django where to find HTML templates
- Context processors add variables to all templates

#### **H. DATABASE - Connection Settings**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',    # MySQL database
        'NAME': 'gram_panchayat_db',             # Database name
        'USER': 'django_user',                   # Database user
        'PASSWORD': 'password123',               # Database password
        'HOST': '127.0.0.1',                     # Database server
        'PORT': '3306',                          # MySQL port
    }
}
```

#### **I. AUTHENTICATION - User Authentication**
```python
AUTH_USER_MODEL = 'portal_app.CustomUser'      # Use custom user model
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LOGIN_URL = 'login'                            # Redirect non-authenticated users
LOGIN_REDIRECT_URL = 'dashboard'               # Where to go after login
```

#### **J. STATIC FILES - CSS, JS, Images**
```python
STATIC_URL = '/static/'                        # URL path for static files
STATIC_ROOT = BASE_DIR / 'staticfiles'         # Where to collect static files
STATICFILES_DIRS = [BASE_DIR / 'static']       # Where to find static files
```

#### **K. MEDIA FILES - User Uploads**
```python
MEDIA_URL = '/media/'                          # URL path for uploads
MEDIA_ROOT = BASE_DIR / 'media'                # Where to store uploads
```

#### **L. SECURITY SETTINGS**
```python
SECURE_BROWSER_XSS_FILTER = True               # Prevent XSS attacks
SECURE_CONTENT_SECURITY_POLICY = {...}        # Content Security Policy
CSRF_COOKIE_SECURE = True                     # CSRF over HTTPS only
SESSION_COOKIE_SECURE = True                  # Session cookies over HTTPS only
X_FRAME_OPTIONS = 'DENY'                      # Prevent clickjacking
```

### **4.3 Settings Management Best Practices**

#### **Problem: Hardcoding Secrets**
```python
# ❌ BAD - Secrets exposed in git
SECRET_KEY = 'my-super-secret-key-123'
DEBUG = True
DB_PASSWORD = 'admin123'
```

#### **Solution: Use Environment Variables**
```python
# ✅ GOOD - Secrets from .env file
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
DB_PASSWORD = config('DB_PASSWORD')
```

Create `.env` file:
```
SECRET_KEY=your-random-secret-key
DEBUG=True
DB_PASSWORD=securepassword123
DB_HOST=localhost
```

Add to `.gitignore`:
```
.env
*.sqlite3
```

### **4.4 Multiple Settings Files (Development vs Production)**

```
grampanchayat/
├── settings/
│   ├── __init__.py
│   ├── base.py              # Common settings
│   ├── development.py       # Development-specific
│   └── production.py        # Production-specific
```

**base.py:**
```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INSTALLED_APPS = [
    'django.contrib.admin',
    ...
]

MIDDLEWARE = [...]
TEMPLATES = [...]
```

**development.py:**
```python
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', ...}}
```

**production.py:**
```python
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
DATABASES = {'default': {'ENGINE': 'django.db.backends.mysql', ...}}
```

**Usage:**
```bash
# Development
python manage.py runserver --settings=grampanchayat.settings.development

# Production
gunicorn grampanchayat.wsgi:application --settings=grampanchayat.settings.production
```

---

## 5. PROJECT VS APP - CRITICAL CONCEPT

### **5.1 Project vs App**

| Project | App |
|---------|-----|
| Top-level container | Reusable component |
| Contains multiple apps | Contains models, views, forms |
| Single per codebase | Multiple per project |
| Example: `grampanchayat` | Example: `portal_app`, `billing_app` |
| Configuration: `settings.py`, `urls.py` | Logic: `models.py`, `views.py` |

### **5.2 Creating an App**

```bash
python manage.py startapp certificates
```

Creates:
```
certificates/
├── __init__.py
├── admin.py
├── apps.py
├── migrations/
├── models.py
├── tests.py
├── views.py
└── urls.py
```

### **5.3 Registering App in settings.py**

Add to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    ...
    'certificates',           # ← Add this
]
```

---

## 6. URLS.PY - URL ROUTING

### **6.1 Project URLs (grampanchayat/urls.py)**

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('portal/', include('portal_app.urls')),      # Include app URLs
    path('certificates/', include('certificates.urls')),
]
```

### **6.2 App URLs (portal_app/urls.py)**

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('apply/birth/', views.apply_birth_certificate, name='apply_birth'),
]
```

### **6.3 URL Flow**

```
User visits: http://localhost:8000/portal/login/
                                   ↓
Django checks grampanchayat/urls.py
  ├── /admin/ → admin interface
  ├── /portal/ → include('portal_app.urls')  ← MATCHES
  └── /certificates/ → ...

Django checks portal_app/urls.py
  ├── '' → home
  ├── 'login/' → login_view  ← MATCHES (/portal/login/)
  ├── 'dashboard/' → dashboard
  └── ...

Execute: views.login_view()
Render: login.html template
```

---

## 7. QUICK START WORKFLOW

```bash
# 1. Create project
django-admin startproject grampanchayat

# 2. Navigate to project
cd grampanchayat

# 3. Create app
python manage.py startapp portal_app

# 4. Define models in portal_app/models.py
# (Edit models.py with your database tables)

# 5. Create migration
python manage.py makemigrations

# 6. Apply migration
python manage.py migrate

# 7. Create admin user
python manage.py createsuperuser

# 8. Run server
python manage.py runserver

# 9. Visit http://localhost:8000/admin/ to see your models
```

---

## 8. SUMMARY TABLE

| Component | File | Purpose |
|-----------|------|---------|
| **Entry Point** | `manage.py` | Django CLI for all commands |
| **Configuration** | `settings.py` | All project settings |
| **URL Routing** | `urls.py` | Map URLs to views |
| **Business Logic** | `views.py` | Handle requests, return responses |
| **Database** | `models.py` | Define database tables |
| **Templates** | `.html` files | Render HTML pages |
| **Static Files** | `static/` | CSS, JavaScript, images |
| **Uploads** | `media/` | User-uploaded files |


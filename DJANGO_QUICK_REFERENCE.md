# 🎨 Django Project Quick Visual Reference

## One-Page Django Overview

```
┌─────────────────────────────────────────────────────────────┐
│           DJANGO PROJECT STRUCTURE AT A GLANCE             │
└─────────────────────────────────────────────────────────────┘

grampanchayat/                      # ← THE PROJECT ROOT
│
├─ manage.py                        # ← RUN ALL COMMANDS HERE
│  │  python manage.py runserver
│  │  python manage.py migrate
│  │  python manage.py shell
│  └─ All Django commands
│
├─ grampanchayat/                   # ← CONFIGURATION PACKAGE
│  ├─ settings.py       ⭐ PROJECT CONFIGURATION
│  │  ├─ INSTALLED_APPS (which apps to use)
│  │  ├─ DATABASES (database connection)
│  │  ├─ SECRET_KEY (security token)
│  │  └─ ... 50+ settings
│  │
│  ├─ urls.py           ⭐ ROOT URL ROUTING
│  │  └─ urlpatterns = [path('admin/'), path('api/', ...)]
│  │
│  ├─ wsgi.py            PRODUCTION SERVER GATEWAY
│  │
│  ├─ asgi.py            ASYNC SERVER GATEWAY
│  │
│  └─ __init__.py        PYTHON PACKAGE MARKER
│
├─ portal_app/                      # ← YOUR APP (reusable component)
│  ├─ models.py         ⭐ DATABASE TABLES
│  │  ├─ class User
│  │  ├─ class Post
│  │  └─ class Comment
│  │
│  ├─ views.py          ⭐ REQUEST HANDLERS
│  │  ├─ def home()
│  │  ├─ def post_detail()
│  │  └─ def add_comment()
│  │
│  ├─ urls.py           ⭐ APP URL ROUTING
│  │  └─ urlpatterns = [path('', home), ...]
│  │
│  ├─ admin.py           REGISTER MODELS IN ADMIN
│  │  └─ admin.site.register(Post)
│  │
│  ├─ forms.py           INPUT FORMS & VALIDATION
│  │
│  ├─ tests.py           UNIT TESTS
│  │
│  ├─ apps.py            APP CONFIGURATION
│  │
│  ├─ migrations/        DATABASE CHANGE HISTORY
│  │  ├─ 0001_initial.py
│  │  └─ 0002_add_field.py
│  │
│  └─ templates/         HTML TEMPLATES FOR THIS APP
│     └─ portal_app/
│        ├─ home.html
│        ├─ post_list.html
│        └─ post_detail.html
│
├─ templates/                       # ← GLOBAL HTML TEMPLATES
│  ├─ base.html
│  ├─ 404.html
│  └─ 500.html
│
├─ static/                          # ← CSS, JS, IMAGES (unchanging)
│  ├─ css/
│  │  ├─ bootstrap.min.css
│  │  └─ style.css
│  ├─ js/
│  │  └─ script.js
│  └─ images/
│     └─ logo.png
│
├─ media/                           # ← USER UPLOADS (changing)
│  ├─ profile_photos/
│  └─ documents/
│
├─ db.sqlite3                       # ← DATABASE FILE (development)
│
├─ requirements.txt                 # ← PYTHON DEPENDENCIES
│
├─ README.md                        # ← DOCUMENTATION
│
└─ .gitignore                       # ← WHAT GIT IGNORES
   └─ .env, *.pyc, __pycache__/
```

---

## Request/Response Flow

```
┌──────────────────┐
│ User in Browser  │
│ http://mysite.com/blog/post/1/
└────────┬─────────┘
         │ HTTP GET
         ▼
┌──────────────────────────────────────┐
│ Django URL Router (urls.py)          │
│ Matches: /blog/post/1/ → view       │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ View Function (views.py)             │
│ def post_detail(request, id):        │
│     post = Post.objects.get(id=id)  │ ← Query DB
│     return render(...)               │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ Template Rendering (template.html)  │
│ <h1>{{ post.title }}</h1>            │
│ {{ post.content }}                   │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ HTML Response                        │
│ <h1>My Blog Post</h1>               │
│ Content here...                      │
└────────┬─────────────────────────────┘
         │ HTTP Response
         ▼
┌──────────────────┐
│ Browser renders  │
│ and shows page   │
└──────────────────┘
```

---

## The MTV Pattern (Django's MVC)

```
          MODEL (models.py)
              ↕
       [Database Tables]
              ↓
              ↓ ORM converts to Python objects
              ↓
          VIEW (views.py)
              ↕
       [Business Logic, Data Processing]
              ↓
              ↓ Pass data to template
              ↓
        TEMPLATE (*.html)
              ↕
       [HTML + Django Tags]
              ↓
              ↓ Render HTML with data
              ↓
        [Rendered Page]
              ↓
              ↓ HTTP Response
              ↓
        USER BROWSER
```

---

## Project Creation Flowchart

```
START
  │
  ▼
┌─────────────────────────────────────┐
│ django-admin startproject myproject │
└────────┬────────────────────────────┘
         │ Creates project structure
         ▼
┌─────────────────────────────────────┐
│ python manage.py startapp myapp     │
└────────┬────────────────────────────┘
         │ Creates app structure
         ▼
┌─────────────────────────────────────┐
│ Edit models.py - Define tables      │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Edit settings.py - Add app          │
│ INSTALLED_APPS = ['myapp']          │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ python manage.py makemigrations     │
└────────┬────────────────────────────┘
         │ Creates migration files
         ▼
┌─────────────────────────────────────┐
│ python manage.py migrate            │
└────────┬────────────────────────────┘
         │ Applies to database
         ▼
┌─────────────────────────────────────┐
│ Edit admin.py - Register models     │
│ admin.site.register(MyModel)        │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Edit views.py - Create logic        │
│ def my_view(request):               │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Create urls.py - Map URLs           │
│ path('', my_view, name='home')      │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Create templates/*.html - Render    │
│ <h1>{{ title }}</h1>                │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ python manage.py runserver          │
└────────┬────────────────────────────┘
         │ Start dev server
         ▼
┌─────────────────────────────────────┐
│ Visit http://localhost:8000/        │
└────────┬────────────────────────────┘
         │
         ▼
        END (Application Running!)
```

---

## File Modification Checklist

When creating a Django project:

```
[ ] 1. Create project
    django-admin startproject myproject

[ ] 2. Create app
    python manage.py startapp myapp

[ ] 3. Edit settings.py
    Add 'myapp' to INSTALLED_APPS

[ ] 4. Edit myapp/models.py
    Define your database tables

[ ] 5. Run makemigrations
    python manage.py makemigrations

[ ] 6. Run migrate
    python manage.py migrate

[ ] 7. Edit myapp/admin.py
    Register your models

[ ] 8. Create myapp/urls.py
    Define URL patterns

[ ] 9. Edit project/urls.py
    Include app URLs

[ ] 10. Edit myapp/views.py
     Define view functions

[ ] 11. Create templates/
     Create HTML files

[ ] 12. Test
     python manage.py runserver

[ ] 13. Visit
     http://localhost:8000/
```

---

## Settings.py Quick Reference

```python
# ══════════════════════════════════════════════════════════════
#                        SECURITY
# ══════════════════════════════════════════════════════════════
SECRET_KEY = 'your-secret-key'              # Change in production!
DEBUG = True                                # False in production!
ALLOWED_HOSTS = ['localhost', 'mysite.com'] # Your domains

# ══════════════════════════════════════════════════════════════
#                     WHAT APPS TO USE
# ══════════════════════════════════════════════════════════════
INSTALLED_APPS = [
    'django.contrib.admin',      # /admin/
    'django.contrib.auth',       # User authentication
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles', # CSS, JS, images
    'myapp',                      # Your custom app
]

# ══════════════════════════════════════════════════════════════
#                    REQUEST PROCESSING
# ══════════════════════════════════════════════════════════════
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',    # Security headers
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',        # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]

# ══════════════════════════════════════════════════════════════
#                       ROUTING
# ══════════════════════════════════════════════════════════════
ROOT_URLCONF = 'myproject.urls'     # Where to find URL patterns

# ══════════════════════════════════════════════════════════════
#                     TEMPLATES (HTML)
# ══════════════════════════════════════════════════════════════
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Where HTML files are
        'APP_DIRS': True,                  # Look in app/templates/
    },
]

# ══════════════════════════════════════════════════════════════
#                      DATABASE
# ══════════════════════════════════════════════════════════════
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # SQLite
        'NAME': BASE_DIR / 'db.sqlite3',         # Database file
    }
}

# ══════════════════════════════════════════════════════════════
#                    STATIC FILES (CSS, JS)
# ══════════════════════════════════════════════════════════════
STATIC_URL = '/static/'                    # URL prefix
STATIC_ROOT = BASE_DIR / 'staticfiles'     # Where to collect
STATICFILES_DIRS = [BASE_DIR / 'static']   # Where to find

# ══════════════════════════════════════════════════════════════
#                    MEDIA FILES (UPLOADS)
# ══════════════════════════════════════════════════════════════
MEDIA_URL = '/media/'              # URL prefix
MEDIA_ROOT = BASE_DIR / 'media'    # Where to store

# ══════════════════════════════════════════════════════════════
#                      AUTHENTICATION
# ══════════════════════════════════════════════════════════════
LOGIN_URL = 'login'                # Redirect non-auth users
LOGIN_REDIRECT_URL = 'home'        # Redirect after login
```

---

## Common Commands at a Glance

```bash
# CREATE
django-admin startproject myproject        # New project
python manage.py startapp myapp            # New app

# DEVELOP
python manage.py runserver                 # Start server
python manage.py shell                     # Interactive Python

# DATABASE
python manage.py makemigrations            # Create migration files
python manage.py migrate                   # Apply to database
python manage.py createsuperuser           # Create admin

# TEST
python manage.py test                      # Run tests
python manage.py check                     # Check configuration

# DEPLOY
python manage.py collectstatic              # Gather static files
python manage.py check --deploy            # Pre-deployment check
```

---

## File Relationships

```
Browser Request
    ↓
┌─────────────────────────────────────┐
│ project/urls.py                     │  ← "Match URL"
│ urlpatterns = [                     │
│   path('blog/', include(...)),  ←─┐ │
│ ]                                │ │
└─────────────────────────────────────┘ │
                                        │
                ┌───────────────────────┘
                │
                ▼
            ┌─────────────────────────────────────┐
            │ app/urls.py                         │  ← "Which view?"
            │ urlpatterns = [                     │
            │   path('post/<id>/', view),  ←──┐  │
            │ ]                               │  │
            └─────────────────────────────────────┘
                                              │
                    ┌─────────────────────────┘
                    │
                    ▼
                ┌─────────────────────────────────────┐
                │ app/views.py                        │  ← "Get data"
                │ def post_detail(request, id):       │
                │     post = Post.objects.get(id)  ←─┼─┐
                │     return render(...)          │  │
                └─────────────────────────────────────┘  │
                                                         │
                    ┌────────────────────────────────────┘
                    │
                    ▼
                ┌─────────────────────────────────────┐
                │ app/models.py                       │  ← "From DB"
                │ class Post(models.Model):           │
                │     title = CharField()             │
                └─────────────────────────────────────┘
                                                │
                                                │
                    ┌───────────────────────────┘
                    │ (data returned)
                    ▼
                ┌─────────────────────────────────────┐
                │ templates/post_detail.html          │  ← "Render HTML"
                │ <h1>{{ post.title }}</h1>           │
                └─────────────────────────────────────┘
                    │
                    ▼
            [HTML sent to browser]
```

---

## Key Differences

```
PROJECT vs APP
──────────────────────────────────────
WHAT IS IT?
  Project:   Entire website/application
  App:       Reusable component

HOW MANY?
  Project:   1 per codebase
  App:       Multiple (0 to many)

CONTAINS WHAT?
  Project:   settings.py, urls.py, apps
  App:       models.py, views.py, templates

EXAMPLE
  Project:   grampanchayat
  App:       certificates, complaints, payments


TEMPLATES vs STATIC FILES
──────────────────────────────────────
TEMPLATES (*.html)
  Location:      templates/
  Content:       HTML with Django tags
  Variable:      {{ variable }}, {% for %}
  Purpose:       Render dynamic pages
  Changes:       Whenever you edit template

STATIC FILES (css, js, images)
  Location:      static/
  Content:       Plain CSS, JS, images
  Variable:      None
  Purpose:       Styling and scripts
  Changes:       Never (after collect)


MIDDLEWARE
──────────────────────────────────────
SecurityMiddleware
  → Adds security headers

SessionMiddleware
  → Manages user sessions

CsrfViewMiddleware
  → Prevents CSRF attacks

AuthenticationMiddleware
  → Handles user login/logout

(Processed in order, top to bottom)
```

---

## One-Minute Recap

✅ **Project** = Container for entire app  
✅ **App** = Reusable component (models, views, templates)  
✅ **manage.py** = Run all Django commands  
✅ **settings.py** = All configuration  
✅ **urls.py** = Match URLs to views  
✅ **models.py** = Database tables  
✅ **views.py** = Handle requests  
✅ **templates/** = HTML files  
✅ **static/** = CSS, JS, images  
✅ **media/** = User uploads  

**Create Project → Create App → Define Models → Create Views → Create Templates → Run Server**


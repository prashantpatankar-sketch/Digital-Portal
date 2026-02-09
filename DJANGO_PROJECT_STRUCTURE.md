# 🎯 Django Project Structure Visual Guide

## Project Directory Tree

```
grampanchayat/                                    # ← Django project root
│
├── manage.py                                    # ← CLI for all Django commands
│                                                #   python manage.py runserver
│                                                #   python manage.py migrate
│                                                #   python manage.py createsuperuser
│
├── db.sqlite3                                   # ← Database (development only)
│
├── grampanchayat/                               # ← Configuration package (IMPORTANT)
│   │
│   ├── __init__.py                              # ← Makes this a Python package
│   │
│   ├── settings.py                              # ⭐ PROJECT SETTINGS
│   │   ├── INSTALLED_APPS              (which apps to use)
│   │   ├── DATABASES                   (database connection)
│   │   ├── SECRET_KEY                  (security token)
│   │   ├── DEBUG                       (dev vs prod)
│   │   ├── TEMPLATES                   (where to find HTML)
│   │   ├── STATIC_URL                  (CSS/JS paths)
│   │   ├── MIDDLEWARE                  (request processors)
│   │   └── ... 50+ other settings
│   │
│   ├── urls.py                                  # ⭐ ROOT URL ROUTING
│   │   └── urlpatterns = [
│   │       path('admin/', admin.site.urls),
│   │       path('portal/', include('portal_app.urls')),
│   │   ]
│   │
│   ├── asgi.py                                  # ← Async Server Gateway Interface
│   │   └── For production async servers (Daphne, Uvicorn)
│   │
│   └── wsgi.py                                  # ← Web Server Gateway Interface
│       └── For production servers (Gunicorn, uWSGI)
│
├── portal_app/                                  # ← Django APP (reusable component)
│   │
│   ├── migrations/                              # ← Database change history
│   │   ├── __init__.py
│   │   ├── 0001_initial.py                      # First migration
│   │   └── 0002_add_field.py                    # Second migration
│   │
│   ├── __init__.py                              # ← Makes this a Python package
│   │
│   ├── admin.py                                 # ← Register models in Django admin
│   │   └── admin.site.register(BirthCertificate)
│   │
│   ├── apps.py                                  # ← App configuration
│   │   └── class PortalAppConfig(AppConfig)
│   │
│   ├── models.py                                # ⭐ DATABASE MODELS
│   │   ├── class CustomUser(AbstractUser)
│   │   ├── class Application(models.Model)
│   │   ├── class BirthCertificate(models.Model)
│   │   └── ... database tables defined as Python classes
│   │
│   ├── views.py                                 # ⭐ BUSINESS LOGIC
│   │   ├── def home(request)                    # View functions
│   │   ├── def login_view(request)              # Handle requests
│   │   ├── def apply_birth_certificate(request)# Return responses
│   │   └── class ApplicationDetailView(DetailView)
│   │
│   ├── forms.py                                 # ← Django forms for validation
│   │   ├── class CitizenRegistrationForm
│   │   ├── class BirthCertificateForm
│   │   └── class LoginForm
│   │
│   ├── tests.py                                 # ← Unit tests
│   │   ├── class CitizenLoginTestCase
│   │   └── class ApplicationSubmissionTest
│   │
│   ├── urls.py                                  # ← APP URL ROUTING
│   │   └── urlpatterns = [
│   │       path('', views.home, name='home'),
│   │       path('login/', views.login_view, name='login'),
│   │   ]
│   │
│   └── templates/                               # ← HTML TEMPLATES
│       └── portal_app/
│           ├── base.html                        # Base template
│           ├── home.html
│           ├── login.html
│           ├── register.html
│           └── dashboard.html
│
├── templates/                                   # ← Global templates (all apps)
│   ├── base.html
│   ├── 404.html
│   └── 500.html
│
├── static/                                      # ← STATIC FILES (never change)
│   ├── css/
│   │   ├── bootstrap.min.css
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── images/
│       └── logo.png
│
├── media/                                       # ← USER UPLOADS (change often)
│   ├── profile_photos/
│   │   └── user_123_profile.jpg
│   ├── certificates/
│   │   └── birth_cert_12345.pdf
│   └── documents/
│       └── aadhar_proof.jpg
│
├── requirements.txt                             # ← Python dependencies
│   ├── Django==4.2.9
│   ├── mysqlclient==2.2.1
│   ├── Pillow==10.1.0
│   └── reportlab==4.0.9
│
├── .env                                         # ← SECRETS (DO NOT COMMIT)
│   ├── SECRET_KEY=xxx
│   ├── DB_PASSWORD=xxx
│   └── DEBUG=True
│
├── .gitignore                                   # ← Tell git what to ignore
│   ├── .env
│   ├── db.sqlite3
│   ├── *.pyc
│   └── __pycache__/
│
├── README.md                                    # ← Project documentation
└── manage.py                                    # ← (duplicate at root level)
```

---

## Request Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER BROWSER                                 │
│              http://localhost:8000/portal/login/                │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP GET request
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              DJANGO URL ROUTER                                  │
│                                                                 │
│  1. Check grampanchayat/urls.py                               │
│     ├─ /admin/       → admin interface                         │
│     ├─ /portal/      → include('portal_app.urls')  ← MATCHES   │
│     └─ /certificates/→ ...                                     │
│                                                                 │
│  2. Check portal_app/urls.py                                   │
│     ├─ ''            → home                                    │
│     ├─ 'login/'      → login_view  ← MATCHES                   │
│     └─ 'dashboard/'  → dashboard                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Call view function
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DJANGO VIEW                                    │
│                                                                 │
│  def login_view(request):                                       │
│      if request.method == 'POST':                               │
│          form = LoginForm(request.POST)                        │
│          if form.is_valid():                                   │
│              user = form.cleaned_data['user']                  │
│              login(request, user)                              │
│              return redirect('dashboard')                      │
│      else:                                                      │
│          form = LoginForm()                                    │
│                                                                 │
│      return render(request, 'portal_app/login.html', {'form': form})
└───────────────────────────┬─────────────────────────────────────┘
                            │ Read template & data
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               TEMPLATE RENDERING                                │
│                                                                 │
│  templates/portal_app/login.html                                │
│  ───────────────────────────────────                            │
│  {% extends 'base.html' %}                                     │
│  {% block content %}                                            │
│    <form method="post">                                         │
│      {% csrf_token %}                                           │
│      {{ form.as_p }}                                            │
│      <button>Login</button>                                     │
│    </form>                                                      │
│  {% endblock %}                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Generate HTML
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   HTML RESPONSE                                 │
│                                                                 │
│  <!DOCTYPE html>                                                │
│  <html>                                                         │
│    <body>                                                       │
│      <form method="post">                                       │
│        <input type="text" name="username" />                    │
│        <input type="password" name="password" />                │
│        <button>Login</button>                                   │
│      </form>                                                    │
│    </body>                                                      │
│  </html>                                                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP Response
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USER BROWSER                                 │
│              [Shows Login Form]                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Settings.py Structure

```
settings.py
│
├── SECURITY SETTINGS
│   ├── SECRET_KEY = 'xxx'              # Sign cookies, tokens
│   ├── DEBUG = True                    # Show errors or not
│   └── ALLOWED_HOSTS = ['localhost']   # Trusted domains
│
├── APP CONFIGURATION
│   ├── INSTALLED_APPS = [              # Which apps to use
│   │   'django.contrib.admin',
│   │   'django.contrib.auth',
│   │   'portal_app',
│   │   'crispy_forms',
│   │]
│   └── MIDDLEWARE = [                  # Request processors
│       'SecurityMiddleware',
│       'SessionMiddleware',
│       'CsrfViewMiddleware',
│   ]
│
├── DATABASE CONFIGURATION
│   └── DATABASES = {                   # Where data lives
│       'default': {
│           'ENGINE': 'django.db.backends.mysql',
│           'NAME': 'gram_panchayat_db',
│           'USER': 'django_user',
│           'PASSWORD': 'password',
│       }
│   }
│
├── TEMPLATES CONFIGURATION
│   └── TEMPLATES = [                   # Where HTML lives
│       {
│           'BACKEND': 'DjangoTemplates',
│           'DIRS': [BASE_DIR / 'templates'],
│           'APP_DIRS': True,
│       }
│   ]
│
├── STATIC FILES CONFIGURATION
│   ├── STATIC_URL = '/static/'         # URL for CSS, JS, images
│   ├── STATIC_ROOT = BASE_DIR / 'staticfiles'
│   └── STATICFILES_DIRS = [BASE_DIR / 'static']
│
├── MEDIA FILES CONFIGURATION
│   ├── MEDIA_URL = '/media/'           # URL for uploads
│   └── MEDIA_ROOT = BASE_DIR / 'media'
│
└── OTHER SETTINGS
    ├── TIME_ZONE = 'UTC'
    ├── LANGUAGE_CODE = 'en-us'
    ├── USE_I18N = True
    └── ... 50+ more settings
```

---

## Django MTV Architecture (Modified MVC)

```
┌────────────────────────────────────────────────────────────────┐
│                   USER BROWSER                                 │
│              (Shows HTML pages)                                │
└───────────────┬──────────────────────────────────┬─────────────┘
                │                                  │
                │ User submits form                │ User clicks link
                │ (POST request)                   │ (GET request)
                │                                  │
                ▼                                  ▼
┌────────────────────────────────────────────────────────────────┐
│                    URL ROUTER (urls.py)                        │
│           Matches URL pattern to view function                │
│                                                               │
│  path('login/', views.login_view, name='login')               │
│  └─ Matches /login/  → Calls login_view()                     │
└───────────────┬────────────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────────────┐
│                   VIEW (views.py)                              │
│        Process request, fetch/update data                     │
│        Return response (HTML or JSON)                         │
│                                                               │
│  def login_view(request):                                     │
│      if request.method == 'POST':                             │
│          form = LoginForm(request.POST)                       │
│          if form.is_valid():                                 │
│              user = authenticate(...)                        │
│              ↓ (uses MODEL)                                   │
│              login(request, user)                            │
│              return render(...)  ← (uses TEMPLATE)            │
└────┬──────────────────┬──────────────────────┬────────────────┘
     │                  │                      │
     │ Fetch/save data  │ Render page         │
     │                  │                      │
     ▼                  ▼                      ▼
┌──────────────┐  ┌──────────────┐  ┌────────────────┐
│  MODEL       │  │  TEMPLATE    │  │  RESPONSE      │
│ (models.py) │  │ (*.html)     │  │  (HTML page)   │
│             │  │              │  │                │
│ class User: │  │ <html>       │  │ <!DOCTYPE>     │
│  username   │  │  <form>      │  │ <html>         │
│  email      │  │   {% for %} │  │  <h1>Login</h1>│
│  password   │  │ </form>      │  │ </html>        │
│             │  │ </html>      │  │                │
└──────────────┘  └──────────────┘  └────────────────┘
     ▲                                      │
     └──────────────────────────────────────┘
              HTTP Response
```

**MTV = Model-Template-View (Django's version of MVC)**

| Component | File | Role |
|-----------|------|------|
| **Model** | `models.py` | Database layer (tables, relationships) |
| **Template** | `.html` files | Presentation layer (what user sees) |
| **View** | `views.py` | Logic layer (process request, fetch data, return response) |

---

## App Lifecycle

```
Step 1: Create App
────────────────
python manage.py startapp certificates
└─ Creates: certificates/ directory with models.py, views.py, etc.

Step 2: Define Models
─────────────────────
Edit certificates/models.py:

class Certificate(models.Model):
    title = models.CharField(max_length=200)
    issued_date = models.DateField()
    
└─ Defines database table structure

Step 3: Create Migration
───────────────────────
python manage.py makemigrations
└─ Creates: certificates/migrations/0001_initial.py
   (Contains: "CREATE TABLE certificates...")

Step 4: Apply Migration
──────────────────────
python manage.py migrate
└─ Executes SQL: CREATE TABLE certificates (...);
   └─ Database now has the table

Step 5: Register in Admin
─────────────────────────
Edit certificates/admin.py:

admin.site.register(Certificate)

└─ Certificate appears in admin at /admin/

Step 6: Create Views
───────────────────
Edit certificates/views.py:

def certificate_list(request):
    certs = Certificate.objects.all()
    return render(request, 'certificates_list.html', {'certs': certs})

└─ Fetches certificates from database

Step 7: Create Templates
────────────────────────
Create certificates/templates/certificates_list.html:

{% for cert in certs %}
    <h2>{{ cert.title }}</h2>
{% endfor %}

└─ Renders certificate list as HTML

Step 8: Add URLs
────────────────
Edit certificates/urls.py:

urlpatterns = [
    path('', views.certificate_list, name='certificate_list'),
]

└─ /certificates/  → certificate_list view

Step 9: Include in Project
──────────────────────────
Edit grampanchayat/urls.py:

urlpatterns = [
    path('certificates/', include('certificates.urls')),
]

└─ /certificates/  now works!

Step 10: Use in Browser
───────────────────────
User visits: http://localhost:8000/certificates/
└─ Sees rendered list of certificates
```

---

## Key File Relationships

```
User Request
    ↓
grampanchayat/urls.py    ← "What view should handle this URL?"
    ↓
portal_app/views.py      ← "Get data and prepare response"
    ↓
portal_app/models.py     ← "Fetch data from database"
    ↓
Database                 ← "Here's the data"
    ↓
portal_app/models.py     ← "Return data to view"
    ↓
portal_app/views.py      ← "Pass data to template"
    ↓
templates/login.html     ← "Render HTML with data"
    ↓
User Browser             ← "Display rendered page"
```


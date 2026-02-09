# Django Apps Quick Start Guide

## 4 Apps Created for Gram Panchayat Portal

Your project now has 4 modular Django apps:

```
✓ accounts     → Login, registration, user profiles
✓ services     → Certificates (birth/death/income), tax payments
✓ complaints   → File and track grievances
✓ dashboard    → Admin panel, statistics, bulk operations
```

---

## Step 1: Update settings.py

Add your apps to `INSTALLED_APPS`:

```python
# grampanchayat/settings.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',      # ← Add this
    'services',      # ← Add this
    'complaints',    # ← Add this
    'dashboard',     # ← Add this
]
```

---

## Step 2: Create urls.py in Each App

Each app needs a `urls.py` file. Create these 4 files:

### accounts/urls.py
```python
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/<int:user_id>/', views.ProfileView.as_view(), name='profile'),
]
```

### services/urls.py
```python
from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.ServicesListView.as_view(), name='list'),
    path('birth-certificate/', views.BirthCertificateCreateView.as_view(), name='birth'),
    path('death-certificate/', views.DeathCertificateCreateView.as_view(), name='death'),
    path('income-certificate/', views.IncomeCertificateCreateView.as_view(), name='income'),
    path('tax/pay/', views.TaxPaymentView.as_view(), name='tax'),
    path('track/<str:ref_id>/', views.TrackApplicationView.as_view(), name='track'),
]
```

### complaints/urls.py
```python
from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    path('', views.ComplaintListView.as_view(), name='list'),
    path('create/', views.ComplaintCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ComplaintDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.ComplaintUpdateView.as_view(), name='update'),
    path('<int:pk>/resolve/', views.ComplaintResolveView.as_view(), name='resolve'),
]
```

### dashboard/urls.py
```python
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='home'),
    path('applications/', views.ApplicationReviewView.as_view(), name='applications'),
    path('complaints/', views.ComplaintManagementView.as_view(), name='complaints'),
    path('users/', views.UserManagementView.as_view(), name='users'),
    path('statistics/', views.StatisticsView.as_view(), name='statistics'),
]
```

---

## Step 3: Update Project URLs

Connect all apps to your project:

```python
# grampanchayat/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('services/', include('services.urls')),
    path('complaints/', include('complaints.urls')),
    path('dashboard/', include('dashboard.urls')),
]
```

---

## Step 4: Define Models

Edit `models.py` in each app (examples):

### accounts/models.py
```python
from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    phone = models.CharField(max_length=10, unique=True)
    aadhar = models.CharField(max_length=12, unique=True)
    village = models.CharField(max_length=100)
    taluka = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
```

### services/models.py
```python
from django.db import models
from accounts.models import CustomUser

class BirthCertificate(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]
    
    applicant = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    child_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    father_name = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'services_birth_certificate'
```

### complaints/models.py
```python
from django.db import models
from accounts.models import CustomUser

class Complaint(models.Model):
    CATEGORIES = [
        ('road', 'Road & Street'), ('water', 'Water Supply'),
        ('health', 'Health'), ('education', 'Education')
    ]
    STATUSES = [
        ('open', 'Open'), ('assigned', 'Assigned'),
        ('resolved', 'Resolved'), ('closed', 'Closed')
    ]
    
    citizen = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORIES)
    status = models.CharField(max_length=20, choices=STATUSES, default='open')
    filed_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'complaints_complaint'
```

### dashboard/models.py
```python
from django.db import models

class SystemLog(models.Model):
    user = models.CharField(max_length=100)
    action = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dashboard_system_log'
```

---

## Step 5: Create Migrations

```bash
# In terminal, from your project root

python manage.py makemigrations accounts
python manage.py makemigrations services
python manage.py makemigrations complaints
python manage.py makemigrations dashboard

# Or make all migrations at once
python manage.py makemigrations
```

Then apply them:
```bash
python manage.py migrate
```

---

## Step 6: Create Views

Edit `views.py` in each app (examples):

### accounts/views.py
```python
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import CustomUser

class RegisterView(View):
    def get(self, request):
        return render(request, 'accounts/register.html')
    
    def post(self, request):
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        return redirect('accounts:login')

class LoginView(View):
    def get(self, request):
        return render(request, 'accounts/login.html')
    
    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            return redirect('dashboard:home')
        return render(request, 'accounts/login.html', {'error': 'Invalid credentials'})

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('accounts:login')
```

### services/views.py
```python
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import BirthCertificate

class BirthCertificateCreateView(LoginRequiredMixin, View):
    login_url = 'accounts:login'
    
    def get(self, request):
        return render(request, 'services/birth_certificate_form.html')
    
    def post(self, request):
        certificate = BirthCertificate.objects.create(
            applicant=request.user,
            child_name=request.POST['child_name'],
            date_of_birth=request.POST['dob'],
            father_name=request.POST['father_name'],
            mother_name=request.POST['mother_name']
        )
        return redirect('services:track', ref_id=certificate.id)
```

### complaints/views.py
```python
from django.views import View
from django.shortcuts import render
from .models import Complaint

class ComplaintCreateView(View):
    def get(self, request):
        return render(request, 'complaints/complaint_form.html')
    
    def post(self, request):
        complaint = Complaint.objects.create(
            citizen=request.user,
            title=request.POST['title'],
            description=request.POST['description'],
            category=request.POST['category']
        )
        return redirect('complaints:detail', pk=complaint.id)
```

---

## Step 7: Create Templates

Create folder structure:
```
accounts/templates/accounts/
├── login.html
├── register.html
└── profile.html

services/templates/services/
├── birth_certificate_form.html
├── track_application.html
└── services_list.html

complaints/templates/complaints/
├── complaint_form.html
├── complaint_list.html
└── complaint_detail.html

dashboard/templates/dashboard/
├── dashboard.html
├── applications.html
└── statistics.html
```

Example template (accounts/templates/accounts/login.html):
```html
{% extends 'base.html' %}

{% block title %}Login{% endblock %}

{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <h2>Login</h2>
            <form method="POST">
                {% csrf_token %}
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" name="username" class="form-control" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary">Login</button>
            </form>
            <p>Don't have account? <a href="{% url 'accounts:register' %}">Register</a></p>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Step 8: Create Forms (Optional but Recommended)

### accounts/forms.py
```python
from django import forms
from .models import CustomUser

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'aadhar', 'village']
    
    def clean(self):
        if self.cleaned_data.get('password') != self.cleaned_data.get('password_confirm'):
            raise forms.ValidationError('Passwords do not match')
        return self.cleaned_data
```

---

## Testing Your Setup

```bash
# Check for errors
python manage.py check

# Run server
python manage.py runserver

# Test specific app
python manage.py test accounts

# Create superuser for admin
python manage.py createsuperuser
```

Then visit: http://127.0.0.1:8000/admin/

---

## URL Structure After Setup

```
/accounts/register/          → Create new user
/accounts/login/             → User login
/accounts/logout/            → User logout
/accounts/profile/123/       → User profile

/services/                   → List all services
/services/birth-certificate/ → Apply for birth certificate
/services/death-certificate/ → Apply for death certificate
/services/income-certificate/→ Apply for income certificate
/services/tax/pay/           → Pay taxes
/services/track/ABC123/      → Track application

/complaints/                 → List complaints
/complaints/create/          → File new complaint
/complaints/123/             → View complaint detail
/complaints/123/update/      → Update complaint

/dashboard/                  → Admin home
/dashboard/applications/     → Review applications
/dashboard/complaints/       → Manage complaints
/dashboard/users/            → Manage users
/dashboard/statistics/       → View stats
```

---

## Common Commands

```bash
# Make migrations after changing models
python manage.py makemigrations

# Apply migrations to database
python manage.py migrate

# See migration status
python manage.py showmigrations

# Run server
python manage.py runserver

# Create superuser
python manage.py createsuperuser

# Interactive shell (test models)
python manage.py shell

# Delete/reset app database
python manage.py migrate <app_name> zero

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test
python manage.py test accounts
```

---

## Benefits You Now Have

✓ **Separation of concerns** - Each app handles one domain
✓ **Easy maintenance** - Changes in accounts don't affect services
✓ **Scalability** - Can load-balance per app later
✓ **Reusability** - Can use accounts app in other projects
✓ **Team collaboration** - Devs can work on different apps
✓ **Testing** - Test each app independently
✓ **Organization** - Clear folder structure
✓ **Database** - Each app manages its own migrations

---

## Need Help?

- See **DJANGO_APP_ARCHITECTURE.md** for detailed info
- See **DJANGO_MYSQL_CONNECTION.md** for database setup
- See **DJANGO_COMMANDS_REFERENCE.md** for all Django commands

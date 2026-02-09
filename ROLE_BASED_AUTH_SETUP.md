# Role-Based Authentication - Setup & Installation Guide

## Prerequisites
- Python 3.8+
- Django 4.2+
- Virtual environment activated
- Database configured (SQLite or MySQL)

---

## Installation Steps

### 1. Apply Migrations
```bash
# Create migration files
python manage.py makemigrations

# Apply migrations to database
python manage.py migrate
```

**Expected Output**:
```
Migrations for 'portal_app':
  portal_app\migrations\0002_alter_customuser_role.py
    - Alter field role on customuser

Operations to perform:
  Apply all migrations: admin, auth, contenttypes, portal_app, sessions
Running migrations:
  Applying portal_app.0002_alter_customuser_role... OK
```

---

### 2. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

Follow prompts to create first admin user.

---

### 3. Install Required Packages (if not already installed)
```bash
pip install argon2-cffi  # For Argon2 password hashing (recommended)
```

Update `requirements.txt`:
```txt
Django>=4.2
django-crispy-forms
crispy-bootstrap5
PyMySQL
python-decouple
argon2-cffi  # Add this line
```

---

### 4. Verify Settings Configuration

Check `gram_panchayat/settings.py` contains:

```python
# Custom User Model
AUTH_USER_MODEL = 'portal_app.CustomUser'

# Middleware with RoleBasedAccessMiddleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'portal_app.middleware.RoleBasedAccessMiddleware',  # ← This line
]

# Password Hashers
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    # ...
]
```

---

### 5. Test the Installation

#### Start Development Server
```bash
python manage.py runserver
```

#### Test URLs
Visit these URLs to verify setup:

1. **Homepage**: http://127.0.0.1:8000/
2. **Register**: http://127.0.0.1:8000/register/
3. **Login**: http://127.0.0.1:8000/login/
4. **Admin Panel**: http://127.0.0.1:8000/admin/

---

## Post-Installation Configuration

### 1. Update Existing Users (if upgrading)

If you have existing users without roles, run this in Django shell:

```bash
python manage.py shell
```

```python
from portal_app.models import CustomUser

# Set all existing users to 'citizen' role
CustomUser.objects.filter(role__isnull=True).update(role='citizen')

# Or manually assign roles
user = CustomUser.objects.get(username='existing_user')
user.role = 'staff'  # or 'admin' or 'citizen'
user.save()

exit()
```

---

### 2. Create Test Users

#### Option A: Via Web Interface
1. Go to http://127.0.0.1:8000/register/
2. Fill form and select role
3. **Citizen**: Can login immediately
4. **Staff/Admin**: Requires approval

#### Option B: Via Django Admin
1. Go to http://127.0.0.1:8000/admin/
2. Login with superuser
3. Navigate to **Users** → **Add User**
4. Set role and is_active=True

#### Option C: Via Django Shell
```bash
python manage.py shell
```

```python
from portal_app.models import CustomUser

# Create citizen (auto-active)
citizen = CustomUser.objects.create_user(
    username='citizen1',
    password='Test@1234',
    first_name='Ramesh',
    last_name='Kumar',
    email='citizen@example.com',
    phone_number='9876543210',
    role='citizen',
    is_active=True,
    address='123 Main Street',
    village='Model Village',
    pincode='123456'
)

# Create staff (needs approval)
staff = CustomUser.objects.create_user(
    username='staff1',
    password='Test@1234',
    first_name='Priya',
    last_name='Sharma',
    email='staff@example.com',
    phone_number='9876543211',
    role='staff',
    is_active=False,  # Pending approval
    address='456 Government Office',
    village='Model Village',
    pincode='123456'
)

# Create admin (needs approval)
admin = CustomUser.objects.create_user(
    username='admin1',
    password='Test@1234',
    first_name='Admin',
    last_name='User',
    email='admin@example.com',
    phone_number='9876543212',
    role='admin',
    is_active=False,  # Pending approval
    address='789 Admin Block',
    village='Model Village',
    pincode='123456'
)

exit()
```

---

### 3. Approve Pending Staff/Admin Accounts

#### Via Django Admin:
1. Login to admin panel: http://127.0.0.1:8000/admin/
2. Go to **Users**
3. Click on pending user (is_active=False)
4. Check **Active** checkbox
5. Save

#### Via Shell:
```python
from portal_app.models import CustomUser

# Activate user by username
user = CustomUser.objects.get(username='staff1')
user.is_active = True
user.save()

# Or activate all pending staff
CustomUser.objects.filter(role='staff', is_active=False).update(is_active=True)
```

---

## Verification Checklist

### ✅ Database
- [ ] Migration `0002_alter_customuser_role` applied successfully
- [ ] CustomUser table has `role` field with max_length=20
- [ ] Existing users have valid roles assigned

### ✅ Files Created/Modified
- [ ] `portal_app/decorators.py` exists
- [ ] `portal_app/middleware.py` exists
- [ ] `portal_app/models.py` updated with 3 roles
- [ ] `portal_app/views.py` updated with decorators
- [ ] `portal_app/forms.py` has validation methods
- [ ] `gram_panchayat/settings.py` has security settings

### ✅ Functionality
- [ ] Can register as Citizen (auto-active)
- [ ] Can register as Staff (pending approval)
- [ ] Can register as Admin (pending approval)
- [ ] Login redirects based on role
- [ ] Citizen cannot access `/admin-dashboard/`
- [ ] Staff can access `/admin-dashboard/`
- [ ] Admin can access all routes
- [ ] Session expires after 1 hour
- [ ] CSRF protection working on forms

### ✅ Security
- [ ] Argon2 password hashing active
- [ ] Password minimum 8 characters enforced
- [ ] HTTP-only cookies enabled
- [ ] CSRF tokens present in forms
- [ ] Inactive users cannot login

---

## Testing Guide

### Test 1: Citizen Registration & Login
```
1. Go to /register/
2. Fill form with role="Citizen"
3. Submit
4. Expected: Success message, redirect to login
5. Login with credentials
6. Expected: Redirect to /citizen-dashboard/
```

### Test 2: Staff Registration (Pending Approval)
```
1. Go to /register/
2. Fill form with role="Panchayat Staff"
3. Submit
4. Expected: Warning message about pending approval
5. Try to login
6. Expected: "Account pending approval" error
7. Approve via admin panel
8. Login again
9. Expected: Success, redirect to /admin-dashboard/
```

### Test 3: Access Control
```
1. Login as Citizen
2. Try to access /admin-dashboard/
3. Expected: "Access denied" error, redirect to home
```

### Test 4: Session Timeout
```
1. Login
2. Wait 1 hour (or adjust SESSION_COOKIE_AGE to 60 seconds for testing)
3. Try to access protected page
4. Expected: Redirect to login
```

### Test 5: CSRF Protection
```
1. Inspect any form (register, login)
2. Expected: Hidden input with name="csrfmiddlewaretoken"
3. Try submitting form without CSRF token
4. Expected: CSRF verification failed error
```

---

## Troubleshooting

### Error: "No module named 'portal_app.decorators'"
**Solution**: Ensure `decorators.py` file exists in `portal_app/` directory

### Error: "No module named 'portal_app.middleware'"
**Solution**: Ensure `middleware.py` file exists in `portal_app/` directory

### Error: "AUTH_USER_MODEL refers to model that has not been installed"
**Solution**: Run migrations: `python manage.py migrate`

### Error: "argon2 not found"
**Solution**: Install argon2: `pip install argon2-cffi`

### Warning: "staticfiles directory does not exist"
**Solution**: Create directory: `mkdir static` (or ignore if not using custom static files)

### Error: "Migration will require a one-way non-nullable column"
**Solution**: Existing users will default to 'citizen' role automatically

---

## Production Deployment Checklist

### Before Deploying:
- [ ] Set `DEBUG = False` in settings.py
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set strong `SECRET_KEY`
- [ ] Enable HTTPS
- [ ] Configure production database (MySQL/PostgreSQL)
- [ ] Run `python manage.py collectstatic`
- [ ] Set environment variables for sensitive data
- [ ] Test all security settings

### Security Settings (Production):
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

---

## Rollback (if needed)

If you need to revert changes:

```bash
# Revert migration
python manage.py migrate portal_app 0001

# Remove migration file
rm portal_app/migrations/0002_alter_customuser_role.py

# Restore previous versions of files from git
git checkout portal_app/models.py
git checkout portal_app/views.py
git checkout portal_app/forms.py
git checkout gram_panchayat/settings.py

# Delete new files
rm portal_app/decorators.py
rm portal_app/middleware.py
```

---

## Support & Documentation

- **Full Documentation**: [ROLE_BASED_AUTHENTICATION.md](ROLE_BASED_AUTHENTICATION.md)
- **Quick Reference**: [ROLE_BASED_AUTH_QUICK_REF.md](ROLE_BASED_AUTH_QUICK_REF.md)
- **Django Docs**: https://docs.djangoproject.com/
- **Security Best Practices**: https://docs.djangoproject.com/en/stable/topics/security/

---

## Next Steps

After successful installation:
1. Create initial admin user via `createsuperuser`
2. Create test users for each role
3. Test all access controls
4. Review security settings
5. Customize templates if needed
6. Set up email notifications (optional)
7. Configure password reset (optional)

---

**Installation Date**: February 6, 2026  
**Version**: 1.0  
**Status**: ✅ Ready for Production

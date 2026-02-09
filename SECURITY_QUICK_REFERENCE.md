# 🔐 Security Quick Reference

## One-Page Security Cheat Sheet

---

## ✅ Security Checklist

### CSRF Protection
- [x] CSRF middleware enabled
- [x] `{% csrf_token %}` in all forms
- [x] HttpOnly cookies
- [x] SameSite='Lax'

### Password Security
- [x] Argon2 hashing
- [x] Min 8 characters
- [x] Password validators
- [x] No plain text storage

### Form Validation
- [x] Email validation
- [x] Phone: 10 digits, starts with 6/7/8/9
- [x] Aadhar: 12 digits
- [x] Pincode: 6 digits
- [x] Username: alphanumeric + underscore

### Role-Based Access
- [x] Middleware protection
- [x] View decorators
- [x] Template-level checks
- [x] URL access control

### SQL Injection Prevention
- [x] Django ORM (auto-protected)
- [x] No raw SQL concatenation
- [x] Parameterized queries only

### XSS Prevention
- [x] Template auto-escaping
- [x] Input sanitization
- [x] No |safe on user input

### File Upload Security
- [x] Size limit: 5MB
- [x] Extension whitelist
- [x] Content-type check
- [x] Filename validation

### Session Security
- [x] 1-hour timeout
- [x] HttpOnly cookies
- [x] Browser-close logout
- [x] HTTPS in production

---

## 🚨 Common Vulnerabilities & Fixes

| Vulnerability | ❌ Bad Code | ✅ Good Code |
|---------------|------------|-------------|
| **SQL Injection** | `f"SELECT * FROM users WHERE id={user_id}"` | `User.objects.filter(id=user_id)` |
| **XSS** | `{{ user.input\|safe }}` | `{{ user.input }}` |
| **CSRF** | `@csrf_exempt` | Keep CSRF protection |
| **Plain Password** | `user.password = "pass"` | `user.set_password("pass")` |
| **Insecure File** | No validation | `validate_file_upload(file)` |

---

## 🔧 Security Utilities

### Import Security Functions
```python
from portal_app.security_utils import (
    sanitize_input,
    validate_file_upload,
    validate_phone_number,
    validate_aadhar_number,
    check_rate_limit,
    log_security_event
)
```

### Common Usage

```python
# Sanitize input
safe_text = sanitize_input(user_input)

# Validate file
validate_file_upload(file, ['.pdf', '.jpg'], max_size=5*1024*1024)

# Check rate limit
if not check_rate_limit(f'login_{ip}', limit=5, period=60):
    return HttpResponse("Too many attempts", status=429)

# Log security event
log_security_event('LOGIN_FAILED', user, f"IP: {ip}", 'WARNING')
```

---

## 🎯 View Protection Decorators

```python
from django.contrib.auth.decorators import login_required
from portal_app.decorators import (
    admin_required,
    staff_required,
    staff_or_admin_required,
    role_required
)

# Any authenticated user
@login_required
def citizen_dashboard(request):
    pass

# Admin only
@admin_required
def admin_dashboard(request):
    pass

# Staff only
@staff_required
def staff_dashboard(request):
    pass

# Staff or Admin
@staff_or_admin_required
def process_application(request):
    pass

# Custom roles
@role_required(['staff', 'admin'])
def manage_system(request):
    pass
```

---

## 📝 Form Validation Example

```python
class MyForm(forms.ModelForm):
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        
        # Validation
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError("Invalid phone number")
        
        if not phone.startswith(('6', '7', '8', '9')):
            raise forms.ValidationError("Invalid phone prefix")
        
        return phone
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        
        # Size check
        if file and file.size > 5 * 1024 * 1024:
            raise forms.ValidationError("File too large (max 5MB)")
        
        # Extension check
        import os
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ['.pdf', '.jpg', '.png']:
            raise forms.ValidationError("Invalid file type")
        
        return file
```

---

## 🔒 Settings Configuration

```python
# settings.py

# Security
DEBUG = False  # Production
SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = ['yourdomain.com']

# CSRF
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Session
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Password Hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    # ... others
]

# Production HTTPS
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
```

---

## 🧪 Security Testing

```bash
# Django security check
python manage.py check --deploy

# Check for vulnerabilities
pip install safety
safety check

# Test in shell
python manage.py shell
>>> from django.contrib.auth.password_validation import validate_password
>>> validate_password("testpass123")
```

---

## 📊 Role Access Matrix

| URL Pattern | Citizen | Staff | Admin |
|-------------|---------|-------|-------|
| `/citizen-dashboard/` | ✅ | ✅ | ✅ |
| `/apply/*` | ✅ | ✅ | ✅ |
| `/staff-dashboard/` | ❌ | ✅ | ✅ |
| `/process/*` | ❌ | ✅ | ✅ |
| `/admin-dashboard/` | ❌ | ❌ | ✅ |
| `/admin/*` | ❌ | ❌ | ✅ |

---

## 🎨 Template Security

```html
<!-- ✅ Good: Auto-escaped -->
<p>{{ user.comment }}</p>

<!-- ❌ Bad: Unsafe -->
<p>{{ user.comment|safe }}</p>

<!-- ✅ Good: CSRF token -->
<form method="POST">
    {% csrf_token %}
    ...
</form>

<!-- ✅ Good: Role check -->
{% if user.role == 'admin' %}
    <a href="/admin/">Admin Panel</a>
{% endif %}
```

---

## 🚨 Production Deployment Checklist

**Before going live:**

- [ ] `DEBUG = False`
- [ ] Strong `SECRET_KEY` (environment variable)
- [ ] Configure `ALLOWED_HOSTS`
- [ ] HTTPS/SSL certificate installed
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] All security headers enabled
- [ ] Database backups configured
- [ ] Run `python manage.py check --deploy`
- [ ] Test all authentication flows
- [ ] Test file upload limits
- [ ] Review user permissions
- [ ] Enable security logging

---

## 📞 Emergency Response

**If security breach detected:**

1. **Isolate**: Disable affected features
2. **Investigate**: Check logs (`log_security_event`)
3. **Fix**: Patch vulnerability
4. **Reset**: Change credentials
5. **Notify**: Inform affected users
6. **Document**: Record incident details

---

## 🔑 Password Requirements

✅ Minimum 8 characters  
✅ Cannot be similar to username  
✅ Cannot be common password  
✅ Cannot be all numeric  
✅ Automatically hashed with Argon2  

---

## 📁 File Upload Rules

| Type | Max Size | Extensions |
|------|----------|------------|
| Images | 2MB | .jpg, .jpeg, .png, .gif |
| Documents | 5MB | .pdf, .doc, .docx |
| Certificates | 5MB | .pdf, .jpg, .png |

---

## 🛡️ Security Middleware Order

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',  # 1
    'django.contrib.sessions.middleware.SessionMiddleware',  # 2
    'django.middleware.common.CommonMiddleware',  # 3
    'django.middleware.csrf.CsrfViewMiddleware',  # 4 - CSRF
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # 5
    'django.contrib.messages.middleware.MessageMiddleware',  # 6
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # 7
    'portal_app.middleware.RoleBasedAccessMiddleware',  # 8 - RBAC
]
```

---

## 💡 Quick Tips

1. **Never disable CSRF** unless you know what you're doing
2. **Always validate user input** on the server side
3. **Use Django ORM** to prevent SQL injection
4. **Keep dependencies updated** regularly
5. **Log security events** for audit trail
6. **Test security** before deploying
7. **Use environment variables** for secrets
8. **Enable HTTPS** in production

---

**Security Status**: 🔒 **PRODUCTION READY**

For detailed documentation, see: [SECURITY_IMPLEMENTATION_GUIDE.md](SECURITY_IMPLEMENTATION_GUIDE.md)

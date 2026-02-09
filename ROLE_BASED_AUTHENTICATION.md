# Role-Based Authentication System

## Overview
This Django portal implements a comprehensive role-based authentication system with three distinct user roles: **Admin**, **Panchayat Staff**, and **Citizen**. Each role has specific permissions and access levels enforced through middleware and decorators.

---

## User Roles

### 1. Admin
- **Full System Access**: Complete control over all features
- **Capabilities**:
  - Review and approve/reject applications
  - Manage all complaints
  - View all user information
  - Approve Staff registrations
  - Access admin dashboard

### 2. Panchayat Staff
- **Management Access**: Can assist with application and complaint management
- **Capabilities**:
  - Review applications
  - Update complaint status
  - View citizen information
  - Access staff dashboard
- **Note**: Staff accounts require admin approval during registration

### 3. Citizen
- **Self-Service Access**: Can apply for services and track progress
- **Capabilities**:
  - Apply for certificates (Birth, Death, Income)
  - Pay taxes
  - File complaints
  - Track application status
  - View personal dashboard

---

## Implementation Components

### 1. Custom User Model (`portal_app/models.py`)

```python
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('citizen', 'Citizen'),
        ('staff', 'Panchayat Staff'),
        ('admin', 'Admin'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    # Additional fields: phone_number, aadhar_number, address, etc.
```

**Key Features**:
- Extended Django's AbstractUser
- Custom role field with three options
- Indian government-compliant fields (Aadhar, phone validation)
- Address fields (village, taluka, district, state, pincode)

---

### 2. Role-Based Middleware (`portal_app/middleware.py`)

**Purpose**: Automatically enforces URL-based access control

**Access Rules**:
| URL Pattern | Allowed Roles |
|------------|---------------|
| `/admin-dashboard/`, `/admin/applications/`, `/admin/review/` | Admin only |
| `/staff-dashboard/`, `/staff/applications/`, `/staff/review/` | Staff, Admin |
| `/citizen-dashboard/`, `/citizen/apply/`, `/citizen/applications/` | All authenticated users |

**How it works**:
- Intercepts every request
- Checks user's role against URL pattern
- Redirects unauthorized users with error message

---

### 3. Role-Based Decorators (`portal_app/decorators.py`)

**Available Decorators**:

#### `@role_required(allowed_roles)`
Generic decorator accepting single role or list of roles
```python
@role_required('admin')
def admin_only_view(request):
    pass

@role_required(['staff', 'admin'])
def staff_or_admin_view(request):
    pass
```

#### `@admin_required`
Shortcut for admin-only views
```python
@admin_required
def sensitive_admin_view(request):
    pass
```

#### `@staff_required`
Shortcut for staff-only views
```python
@staff_required
def staff_management_view(request):
    pass
```

#### `@citizen_required`
Shortcut for citizen-only views
```python
@citizen_required
def apply_certificate_view(request):
    pass
```

#### `@staff_or_admin_required`
Shortcut for staff or admin views
```python
@staff_or_admin_required
def review_application_view(request):
    pass
```

---

### 4. Enhanced Registration (`portal_app/forms.py` & `portal_app/views.py`)

#### Registration Form Features
```python
class CitizenRegistrationForm(UserCreationForm):
    # Role selection with all three options
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES)
    
    # Validation methods:
    - clean_email() - Ensures email uniqueness
    - clean_phone_number() - Validates 10-digit Indian mobile
    - clean_aadhar_number() - Validates 12-digit Aadhar
```

#### Registration Security
- **Citizens**: Immediately active, can login after registration
- **Staff & Admin**: 
  - Account created as **inactive** (`is_active=False`)
  - Requires admin approval before login
  - User notified of pending approval status

```python
if role in ['admin', 'staff']:
    user.is_active = False  # Requires approval
else:
    user.is_active = True   # Citizens auto-approved
```

---

### 5. Role-Based Login & Redirects

#### Login Flow
1. User enters credentials
2. System authenticates user
3. **Active Status Check**: Inactive users (pending approval) cannot login
4. **Role-Based Redirect**:
   - Admin → `/admin-dashboard/`
   - Staff → `/admin-dashboard/`
   - Citizen → `/citizen-dashboard/`

```python
if user.role == 'admin':
    return redirect('admin_dashboard')
elif user.role == 'staff':
    return redirect('admin_dashboard')
else:
    return redirect('dashboard')
```

---

## Security Best Practices Implemented

### 1. Password Security
```python
# settings.py
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',  # Most secure
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    # ...
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
```

### 2. Session Security
```python
SESSION_COOKIE_AGE = 3600                    # 1 hour timeout
SESSION_SAVE_EVERY_REQUEST = True            # Extend on activity
SESSION_EXPIRE_AT_BROWSER_CLOSE = True       # Auto-logout on close
SESSION_COOKIE_HTTPONLY = True               # Prevent XSS attacks
SESSION_COOKIE_SAMESITE = 'Lax'              # CSRF protection
```

### 3. CSRF Protection
```python
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_NAME = 'gram_panchayat_csrftoken'
```

### 4. Production Security (when DEBUG=False)
```python
SECURE_SSL_REDIRECT = True                   # Force HTTPS
SESSION_COOKIE_SECURE = True                 # HTTPS-only cookies
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True             # XSS protection
SECURE_CONTENT_TYPE_NOSNIFF = True           # Prevent MIME sniffing
X_FRAME_OPTIONS = 'DENY'                     # Prevent clickjacking
SECURE_HSTS_SECONDS = 31536000               # HTTP Strict Transport Security
```

### 5. Input Validation
- Phone number: 10 digits, starts with 6-9
- Aadhar: Exactly 12 digits
- Pincode: Exactly 6 digits
- Email: Unique across system
- All user inputs sanitized through Django forms

---

## Usage Examples

### Protecting a Citizen View
```python
from portal_app.decorators import citizen_required

@citizen_required
def apply_birth_certificate(request):
    # Only citizens can access
    # Automatically redirected if not citizen role
    ...
```

### Protecting an Admin/Staff View
```python
from portal_app.decorators import staff_or_admin_required

@staff_or_admin_required
def review_application(request, application_id):
    # Only staff or admin can access
    ...
```

### Manual Role Check (if needed)
```python
@login_required
def some_view(request):
    if request.user.role == 'admin':
        # Admin-specific logic
        pass
    elif request.user.role == 'staff':
        # Staff-specific logic
        pass
    else:
        # Citizen logic
        pass
```

---

## Database Migration

After implementing the role-based system, run:

```bash
# Create migration for role field update
python manage.py makemigrations

# Apply migration
python manage.py migrate

# Migration created: 0002_alter_customuser_role.py
```

---

## Testing the System

### 1. Create Test Users

#### Via Django Admin:
```bash
python manage.py createsuperuser
```

#### Via Registration Page:
- **Citizen**: Register and login immediately
- **Staff/Admin**: Register, then have admin activate account

### 2. Test Role Access

#### Citizen Access:
- ✅ Can access: `/citizen-dashboard/`, `/citizen/apply/`
- ❌ Cannot access: `/admin-dashboard/`, `/admin/applications/`

#### Staff Access:
- ✅ Can access: `/admin-dashboard/`, `/admin/applications/`
- ❌ Cannot access: Citizen-specific operations (if restricted)

#### Admin Access:
- ✅ Can access: All routes

### 3. Verify Security
- [ ] Inactive accounts cannot login
- [ ] Session expires after 1 hour
- [ ] CSRF tokens present in all forms
- [ ] Unauthorized access redirects with error message
- [ ] Password strength enforced (min 8 chars)

---

## Admin Approval Workflow

### Approving Staff/Admin Accounts

1. **Via Django Admin Panel** (`/admin/`):
   - Navigate to Users
   - Find pending user (is_active=False)
   - Check "Active" checkbox
   - Save

2. **Via Custom Admin Dashboard** (to be implemented):
   - View pending registrations
   - Review applicant details
   - Approve/Reject with one click

---

## Configuration

### Required Settings (`settings.py`)

```python
# Custom User Model
AUTH_USER_MODEL = 'portal_app.CustomUser'

# Middleware (order matters!)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'portal_app.middleware.RoleBasedAccessMiddleware',  # Add this
]

# Login URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'
```

---

## Troubleshooting

### Issue: "Access denied" when accessing valid route
**Solution**: Check if user's role matches the required role. Verify decorator is correct.

### Issue: Staff registration not working
**Solution**: Ensure `is_active=False` is set correctly. Admin must manually activate.

### Issue: Middleware blocking legitimate requests
**Solution**: Check path patterns in `middleware.py`. Update path list if new routes added.

### Issue: Session expires too quickly
**Solution**: Increase `SESSION_COOKIE_AGE` in settings.py (currently 3600 seconds = 1 hour)

### Issue: CSRF verification failed
**Solution**: 
- Ensure `{% csrf_token %}` in all POST forms
- Check CSRF cookie settings
- Verify middleware order

---

## Future Enhancements

- [ ] Role-based permissions using Django Guardian
- [ ] Two-factor authentication (2FA)
- [ ] Email verification on registration
- [ ] SMS OTP for sensitive operations
- [ ] Audit logging for admin actions
- [ ] Password reset with security questions
- [ ] Account lockout after failed attempts
- [ ] IP-based access restrictions

---

## File Structure

```
portal_app/
├── models.py              # CustomUser with role field
├── forms.py               # CitizenRegistrationForm with validation
├── views.py               # Role-based login/registration views
├── decorators.py          # Role-based decorators (NEW)
├── middleware.py          # RoleBasedAccessMiddleware (NEW)
├── migrations/
│   ├── 0001_initial.py
│   └── 0002_alter_customuser_role.py  # Role field update (NEW)
└── templates/
    └── portal_app/
        ├── register.html   # Updated with role selection
        └── login.html

gram_panchayat/
└── settings.py            # Security settings updated
```

---

## Summary

✅ **Implemented**:
- Custom User Model with 3 roles
- Role-based middleware for URL protection
- Role-based decorators for view protection
- Enhanced registration with approval workflow
- Role-based login redirects
- Comprehensive security settings
- Session management
- CSRF protection
- Password strength validation

✅ **Security Best Practices**:
- Argon2 password hashing
- HTTP-only cookies
- HTTPS enforcement (production)
- Session timeout
- CSRF tokens
- Input validation
- XSS protection
- Clickjacking prevention

✅ **User Experience**:
- Clear error messages
- Automatic role-based redirects
- Pending approval notifications
- Intuitive registration flow

---

**Created**: February 6, 2026  
**Version**: 1.0  
**Django Version**: 4.2+  
**Python Version**: 3.8+

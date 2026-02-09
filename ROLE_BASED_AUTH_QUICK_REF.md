# Role-Based Authentication - Quick Reference

## User Roles & Access Levels

| Role | Description | Auto-Approved? | Dashboard URL |
|------|-------------|----------------|---------------|
| **Citizen** | General public user | ✅ Yes | `/citizen-dashboard/` |
| **Panchayat Staff** | Government employee | ❌ Needs approval | `/admin-dashboard/` |
| **Admin** | System administrator | ❌ Needs approval | `/admin-dashboard/` |

---

## Decorator Quick Reference

```python
# Import decorators
from portal_app.decorators import (
    role_required,
    admin_required,
    staff_required,
    citizen_required,
    staff_or_admin_required
)

# Usage examples
@admin_required
def admin_view(request): ...

@staff_or_admin_required
def review_view(request): ...

@citizen_required
def apply_view(request): ...

@role_required(['citizen', 'staff'])
def mixed_access_view(request): ...
```

---

## Common Tasks

### Register a New User
1. Navigate to `/register/`
2. Fill out form and select role
3. **If Citizen**: Login immediately
4. **If Staff/Admin**: Wait for admin approval

### Approve Staff/Admin Account
1. Login as admin
2. Go to Django Admin (`/admin/`)
3. Navigate to **Users**
4. Find user with `is_active=False`
5. Check **Active** checkbox and save

### Check Current User Role (in templates)
```html
{% if request.user.role == 'admin' %}
    <p>Welcome, Admin!</p>
{% elif request.user.role == 'staff' %}
    <p>Welcome, Staff!</p>
{% else %}
    <p>Welcome, Citizen!</p>
{% endif %}
```

### Check Current User Role (in views)
```python
if request.user.role == 'admin':
    # Admin logic
elif request.user.role == 'staff':
    # Staff logic
else:
    # Citizen logic
```

---

## Security Settings Summary

| Setting | Value | Purpose |
|---------|-------|---------|
| Session Timeout | 1 hour | Auto-logout after inactivity |
| Password Min Length | 8 characters | Strong passwords |
| Password Hasher | Argon2 | Most secure hashing |
| CSRF Protection | ✅ Enabled | Prevent CSRF attacks |
| HTTP-Only Cookies | ✅ Enabled | Prevent XSS |
| HTTPS (Production) | ✅ Enabled | Encrypted traffic |

---

## URL Access Matrix

| URL Pattern | Citizen | Staff | Admin |
|------------|---------|-------|-------|
| `/register/` | ✅ | ✅ | ✅ |
| `/login/` | ✅ | ✅ | ✅ |
| `/citizen-dashboard/` | ✅ | ✅ | ✅ |
| `/citizen/apply/` | ✅ | ❌ | ❌ |
| `/admin-dashboard/` | ❌ | ✅ | ✅ |
| `/admin/applications/` | ❌ | ✅ | ✅ |
| `/admin/review/` | ❌ | ✅ | ✅ |

---

## Validation Rules

### Phone Number
- Exactly 10 digits
- Must start with 6, 7, 8, or 9
- Must be unique

### Aadhar Number
- Exactly 12 digits
- Must be unique (if provided)
- Optional field

### Email
- Valid email format
- Must be unique

### Pincode
- Exactly 6 digits

### Password
- Minimum 8 characters
- Cannot be too similar to username
- Cannot be a common password
- Cannot be entirely numeric

---

## Migration Commands

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations portal_app
```

---

## Test Scenarios

### ✅ Should Work
- Citizen registers and logs in immediately
- Staff registers but cannot login (pending approval)
- Admin approves staff account
- Citizen accesses citizen dashboard
- Staff accesses admin dashboard
- Admin accesses all routes
- Session expires after 1 hour

### ❌ Should Fail
- Citizen accessing `/admin-dashboard/`
- Staff with `is_active=False` logging in
- Duplicate email registration
- Duplicate phone number registration
- Password less than 8 characters
- Phone number starting with 5

---

## Files Modified/Created

✅ **Modified**:
- `portal_app/models.py` - Added 'staff' role
- `portal_app/forms.py` - Enhanced validation
- `portal_app/views.py` - Role-based redirects
- `gram_panchayat/settings.py` - Security settings

✅ **Created**:
- `portal_app/decorators.py` - Role decorators
- `portal_app/middleware.py` - Access middleware
- `portal_app/migrations/0002_alter_customuser_role.py`
- `ROLE_BASED_AUTHENTICATION.md` - Full documentation
- `ROLE_BASED_AUTH_QUICK_REF.md` - This file

---

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| "Access denied" error | Check user role matches decorator |
| Cannot login after registration | Check `is_active` status (staff/admin need approval) |
| CSRF error | Add `{% csrf_token %}` to form |
| Session expires too fast | Increase `SESSION_COOKIE_AGE` |
| Middleware blocking requests | Update path patterns in middleware.py |

---

## Support

For detailed information, see: [ROLE_BASED_AUTHENTICATION.md](ROLE_BASED_AUTHENTICATION.md)

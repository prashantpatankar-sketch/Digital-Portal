# Role-Based Authentication - Visual Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Digital Gram Panchayat Portal                │
│                  Role-Based Authentication                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────┐
         │      User Registration              │
         │   (All roles can register)          │
         └────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
    ┌─────────────────┐           ┌─────────────────┐
    │    CITIZEN      │           │  STAFF / ADMIN  │
    │  is_active=True │           │ is_active=False │
    │ (Auto-approved) │           │ (Needs approval)│
    └─────────────────┘           └─────────────────┘
              │                               │
              │                               ▼
              │                   ┌─────────────────────┐
              │                   │  Admin Approves     │
              │                   │  is_active=True     │
              │                   └─────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   LOGIN PAGE     │
                    └──────────────────┘
                              │
                              ▼
              ┌───────────────┴────────────────┐
              │                                │
    ┌─────────▼─────────┐         ┌───────────▼────────┐
    │  CITIZEN ROLE     │         │  STAFF/ADMIN ROLE  │
    │  ↓                │         │  ↓                 │
    │  /citizen-        │         │  /admin-           │
    │  dashboard/       │         │  dashboard/        │
    └───────────────────┘         └────────────────────┘
```

---

## Role Hierarchy & Permissions

```
                    ┌─────────────┐
                    │    ADMIN    │ ← Highest Authority
                    │  (Full)     │
                    └──────┬──────┘
                           │
                           │ Can approve Staff
                           │
                    ┌──────▼──────┐
                    │    STAFF    │ ← Management
                    │ (Panchayat) │
                    └──────┬──────┘
                           │
                           │ Can review applications
                           │
                    ┌──────▼──────┐
                    │   CITIZEN   │ ← General Public
                    │  (Public)   │
                    └─────────────┘
```

### Permission Matrix

```
Feature                    │ Citizen │ Staff │ Admin │
──────────────────────────────────────────────────────
Register (Auto-approve)    │    ✅   │   ❌  │   ❌  │
Register (Need approval)   │    ❌   │   ✅  │   ✅  │
──────────────────────────────────────────────────────
Apply Certificates         │    ✅   │   ❌  │   ❌  │
Pay Taxes                  │    ✅   │   ❌  │   ❌  │
File Complaints            │    ✅   │   ✅  │   ✅  │
Track Applications         │    ✅   │   ❌  │   ❌  │
──────────────────────────────────────────────────────
View All Applications      │    ❌   │   ✅  │   ✅  │
Review Applications        │    ❌   │   ✅  │   ✅  │
Approve/Reject Apps        │    ❌   │   ✅  │   ✅  │
──────────────────────────────────────────────────────
View All Complaints        │    ❌   │   ✅  │   ✅  │
Update Complaint Status    │    ❌   │   ✅  │   ✅  │
──────────────────────────────────────────────────────
Approve Staff Accounts     │    ❌   │   ❌  │   ✅  │
Manage Users               │    ❌   │   ❌  │   ✅  │
System Configuration       │    ❌   │   ❌  │   ✅  │
──────────────────────────────────────────────────────
```

---

## Authentication Flow Diagram

```
START
  │
  ▼
┌──────────────┐
│ User visits  │
│  /register/  │
└──────┬───────┘
       │
       ▼
┌─────────────────────────┐
│ Fill Registration Form  │
│ • Username              │
│ • Email                 │
│ • Password              │
│ • Phone                 │
│ • Select ROLE           │
└──────┬──────────────────┘
       │
       ▼
    Role?
       │
   ┌───┴────┬──────────┐
   │        │          │
Citizen   Staff     Admin
   │        │          │
   ▼        ▼          ▼
Active=T  Active=F  Active=F
   │        │          │
   ▼        ▼          ▼
Can      Pending   Pending
Login    Approval  Approval
   │        │          │
   │        └────┬─────┘
   │             │
   │             ▼
   │      ┌─────────────┐
   │      │Admin Panel  │
   │      │Approves     │
   │      │Account      │
   │      └──────┬──────┘
   │             │
   │             ▼
   │        Active=True
   │             │
   └─────┬───────┘
         │
         ▼
  ┌─────────────┐
  │ LOGIN PAGE  │
  └──────┬──────┘
         │
         ▼
  ┌──────────────────┐
  │ Authenticate     │
  │ Check is_active  │
  └──────┬───────────┘
         │
         ▼
    Success?
         │
    ┌────┴────┐
   No        Yes
    │          │
    ▼          ▼
  Error    Check Role
  Msg          │
    │      ┌───┴───┬──────┐
    │      │       │      │
    │   Citizen Staff  Admin
    │      │       │      │
    │      ▼       ▼      ▼
    │   /citizen /admin /admin
    │   -dash   -dash  -dash
    │      │       │      │
    └──────┴───────┴──────┘
                 │
                 ▼
          ┌─────────────┐
          │  Dashboard  │
          └─────────────┘
```

---

## Access Control Flow

```
User Request
     │
     ▼
┌──────────────────┐
│  URL Requested   │
│  /some/path/     │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│  RoleBasedAccess         │
│  Middleware              │
│  (Checks URL pattern)    │
└────────┬─────────────────┘
         │
         ▼
    Matches
  Admin URL?
         │
    ┌────┴────┐
   Yes       No
    │         │
    ▼         ▼
 Role=    Continue
 Admin?      │
    │         │
  ┌─┴─┐       │
 No  Yes      │
  │   │       │
  ▼   │       │
Deny  │       │
  │   │       │
  └───┼───────┘
      │
      ▼
┌──────────────────┐
│  View Decorator  │
│  @role_required  │
└────────┬─────────┘
         │
         ▼
   Role Match?
         │
    ┌────┴────┐
   No        Yes
    │         │
    ▼         ▼
 Redirect  Execute
 to Home    View
    │         │
    ▼         ▼
  Error    Success
  Message  Response
```

---

## Security Layers

```
┌─────────────────────────────────────────────┐
│          Layer 1: Registration              │
│  • Email/Phone/Aadhar uniqueness            │
│  • Password strength (min 8 chars)          │
│  • Input validation                         │
│  • Auto-approval for Citizens only          │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│          Layer 2: Authentication            │
│  • Argon2 password hashing                  │
│  • is_active status check                   │
│  • Session creation (1-hour timeout)        │
│  • HTTP-only cookies                        │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│          Layer 3: Authorization             │
│  • Middleware URL pattern checking          │
│  • View decorator role verification         │
│  • CSRF token validation                    │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│          Layer 4: Session Security          │
│  • Session timeout (1 hour)                 │
│  • Auto-extend on activity                  │
│  • Expire on browser close                  │
│  • SameSite cookie policy                   │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│          Layer 5: Transport Security        │
│  • HTTPS enforcement (production)           │
│  • HSTS header (1 year)                     │
│  • Secure cookies (production)              │
│  • XSS & Clickjacking protection            │
└─────────────────────────────────────────────┘
```

---

## Data Flow: Registration to Dashboard

```
┌──────────┐       ┌──────────┐       ┌──────────┐
│  Citizen │       │  Staff   │       │  Admin   │
│  Regis.  │       │  Regis.  │       │  Regis.  │
└────┬─────┘       └────┬─────┘       └────┬─────┘
     │                  │                    │
     ▼                  ▼                    ▼
  role=              role=                role=
 'citizen'          'staff'              'admin'
     │                  │                    │
     ▼                  ▼                    ▼
is_active=T        is_active=F          is_active=F
     │                  │                    │
     ▼                  ▼                    ▼
  ┌─────┐          ┌─────────┐          ┌─────────┐
  │READY│          │PENDING  │          │PENDING  │
  │LOGIN│          │APPROVAL │          │APPROVAL │
  └──┬──┘          └────┬────┘          └────┬────┘
     │                  │                    │
     │                  └─────────┬──────────┘
     │                            │
     │                            ▼
     │                     ┌─────────────┐
     │                     │Admin Portal │
     │                     │  Activates  │
     │                     └──────┬──────┘
     │                            │
     │                            ▼
     │                       is_active=T
     │                            │
     └────────────┬───────────────┘
                  │
                  ▼
            ┌──────────┐
            │  LOGIN   │
            └────┬─────┘
                 │
                 ▼
         Role-based redirect
                 │
     ┌───────────┼───────────┐
     │           │           │
     ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Citizen │ │  Staff  │ │  Admin  │
│Dashboard│ │Dashboard│ │Dashboard│
└─────────┘ └─────────┘ └─────────┘
```

---

## URL Access Map

```
Public URLs (No login required)
├── /
├── /about/
├── /services/
├── /register/
└── /login/

Citizen URLs (role='citizen')
├── /citizen-dashboard/
├── /citizen/apply/
│   ├── birth-certificate/
│   ├── death-certificate/
│   └── income-certificate/
├── /citizen/applications/
├── /citizen/complaints/
└── /citizen/track/

Staff URLs (role='staff' or 'admin')
├── /admin-dashboard/
├── /admin/applications/
├── /admin/review/<id>/
├── /admin/complaints/
└── /admin/update-complaint/<id>/

Admin URLs (role='admin' only)
├── /admin/users/
├── /admin/approve-staff/
└── /admin/ (Django Admin)
```

---

## Decorator Usage Guide

```python
# Citizen-only views
@citizen_required
def apply_certificate(request):
    pass

# Staff-only views
@staff_required
def staff_panel(request):
    pass

# Admin-only views
@admin_required
def system_config(request):
    pass

# Staff OR Admin
@staff_or_admin_required
def review_application(request, app_id):
    pass

# Multiple roles (custom)
@role_required(['citizen', 'staff'])
def view_public_data(request):
    pass

# Generic with list
@role_required(['staff', 'admin'])
def management_view(request):
    pass
```

---

## Session Lifecycle

```
Login
  │
  ▼
┌──────────────────┐
│ Session Created  │
│ • ID generated   │
│ • Cookie set     │
│ • Timeout: 1hr   │
└────────┬─────────┘
         │
         ▼
    Activity?
         │
    ┌────┴────┐
   Yes       No
    │         │
    ▼         ▼
 Extend    Countdown
 Timer       │
    │         ▼
    │     60 mins
    │      passed?
    │         │
    │     ┌───┴───┐
    │    No      Yes
    │     │       │
    └─────┘       ▼
              ┌─────────┐
              │ Expired │
              │ Logout  │
              └─────────┘

Browser Closed
  │
  ▼
Session
Deleted
```

---

## Error Handling Flow

```
User Action
     │
     ▼
  Validation
     │
     ▼
  Errors?
     │
  ┌──┴──┐
 No    Yes
  │     │
  │     ▼
  │  ┌─────────────────┐
  │  │ Form Errors     │
  │  │ • Email exists  │
  │  │ • Invalid phone │
  │  │ • Weak password │
  │  └────────┬────────┘
  │           │
  │           ▼
  │      Display Error
  │           │
  │           ▼
  │      Stay on Page
  │
  ▼
Success
  │
  ▼
Process
Request
```

---

## Implementation Checklist (Visual)

```
☑ Models
  ├─ ✅ CustomUser with role field
  ├─ ✅ ROLE_CHOICES (3 roles)
  └─ ✅ Validation fields

☑ Forms
  ├─ ✅ CitizenRegistrationForm
  ├─ ✅ clean_email()
  ├─ ✅ clean_phone_number()
  └─ ✅ clean_aadhar_number()

☑ Views
  ├─ ✅ register_view (role-based activation)
  ├─ ✅ login_view (role-based redirect)
  ├─ ✅ logout_view
  └─ ✅ Decorators applied

☑ Middleware
  └─ ✅ RoleBasedAccessMiddleware

☑ Decorators
  ├─ ✅ @role_required
  ├─ ✅ @admin_required
  ├─ ✅ @staff_required
  ├─ ✅ @citizen_required
  └─ ✅ @staff_or_admin_required

☑ Settings
  ├─ ✅ AUTH_USER_MODEL
  ├─ ✅ MIDDLEWARE
  ├─ ✅ PASSWORD_HASHERS
  ├─ ✅ SESSION_* settings
  └─ ✅ Security settings

☑ Migrations
  └─ ✅ 0002_alter_customuser_role

☑ Documentation
  ├─ ✅ ROLE_BASED_AUTHENTICATION.md
  ├─ ✅ ROLE_BASED_AUTH_QUICK_REF.md
  ├─ ✅ ROLE_BASED_AUTH_SETUP.md
  ├─ ✅ IMPLEMENTATION_SUMMARY.md
  └─ ✅ ROLE_BASED_AUTH_VISUAL_GUIDE.md
```

---

## Quick Decision Tree: "Can User Access?"

```
                     START
                       │
                       ▼
                 Logged in?
                       │
                  ┌────┴────┐
                 No        Yes
                  │          │
                  ▼          ▼
              Login Pg   Is Active?
                           │
                      ┌────┴────┐
                     No        Yes
                      │          │
                      ▼          ▼
                  Pending    Get Role
                  Msg           │
                           ┌────┴────┬─────────┐
                           │         │         │
                        Citizen   Staff     Admin
                           │         │         │
                           ▼         ▼         ▼
                        /citizen  /admin    /admin
                        routes    routes    +
                           │         │      /admin/*
                           │         │         │
                           └────┬────┴─────────┘
                                │
                                ▼
                         URL matches
                         allowed role?
                                │
                           ┌────┴────┐
                          Yes       No
                           │          │
                           ▼          ▼
                        ALLOW      DENY
                        Access    Redirect
```

---

**Visual Guide Version**: 1.0  
**Created**: February 6, 2026  
**Status**: Complete

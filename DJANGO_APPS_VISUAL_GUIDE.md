# Django Apps: Visual Guide & Commands

## 4 Apps Created in Your Project

```
┌──────────────────────────────────────────────────────────────┐
│                  Gram Panchayat Portal                        │
│              (grampanchayat_demo/grampanchayat/)              │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ URL Routing
                            ▼
        ┌───────────┬───────────┬───────────┬───────────┐
        │           │           │           │           │
    /accounts/   /services/   /complaints/  /dashboard/
        │           │           │           │
        ▼           ▼           ▼           ▼
    ┌─────────┐┌────────────┐┌──────────┐┌──────────┐
    │ accounts││  services  ││complaints││dashboard │
    │         ││            ││          ││          │
    │ LOGIN   ││ CERT.      ││ GRIEVANCE││  ADMIN   │
    │ REG.    ││ APPLY      ││ FILE     ││ PANEL    │
    │ PROFILE ││ PAY TAX    ││ TRACK    ││ STATS    │
    │         ││ TRACK      ││ RESOLVE  ││ REPORTS  │
    └─────────┘└────────────┘└──────────┘└──────────┘
```

---

## App File Structure

Each app created has this structure:

```
app_name/
├── __init__.py                  # Makes it a Python package
├── admin.py                     # Django admin configuration
├── apps.py                      # App configuration metadata
├── models.py                    # Database models
├── views.py                     # View functions/classes
├── urls.py                      # URL patterns (YOU CREATE THIS)
├── forms.py                     # Forms for user input (YOU CREATE THIS)
├── tests.py                     # Unit tests
├── migrations/                  # Database schema history
│   └── __init__.py
├── templates/app_name/          # HTML templates (YOU CREATE THIS)
│   ├── list.html
│   ├── detail.html
│   └── form.html
└── static/app_name/             # CSS, JS, images (YOU CREATE THIS)
    ├── css/
    ├── js/
    └── images/
```

---

## 1. ACCOUNTS App (Authentication)

### Purpose
User login, registration, password reset, profile management

### Models
```
CustomUser
├── username (unique)
├── email (unique)
├── password (hashed)
├── phone (unique)
├── aadhar (unique)
├── village
├── taluka
├── district
├── state
└── is_active

UserProfile
├── user (ForeignKey → CustomUser)
├── profile_photo
├── bio
└── verified (bool)
```

### URLs
```
/accounts/register/           # GET: Show form, POST: Create user
/accounts/login/              # GET: Show login form, POST: Authenticate
/accounts/logout/             # GET: Logout user
/accounts/profile/123/        # GET: Show profile, POST: Update profile
/accounts/password-reset/     # GET: Show reset form, POST: Send email
/accounts/password-reset-confirm/<token>/  # Confirm password reset
```

### Views (Functions)
```
RegisterView.get()  → Show registration form
RegisterView.post() → Save new user to database

LoginView.get()  → Show login form
LoginView.post() → Authenticate user, create session

LogoutView.get() → Destroy session, redirect to login

ProfileView.get()  → Show user profile
ProfileView.post() → Update profile info
```

### Forms
```
UserRegistrationForm
├── username
├── email
├── password
├── password_confirm
├── phone
└── aadhar

LoginForm
├── username
└── password

ProfileUpdateForm
├── phone
├── village
├── taluka
├── district
└── state
```

### Templates
```
accounts/templates/accounts/
├── register.html           (Registration form)
├── login.html              (Login form)
├── profile.html            (User profile page)
├── password_reset.html     (Password reset form)
└── password_reset_email.html (Email template)
```

---

## 2. SERVICES App (Certificates & Taxes)

### Purpose
Apply for certificates (birth, death, income), pay taxes, track applications

### Models
```
Certificate (Base)
├── application_id (unique)
├── applicant (FK → User)
├── status (pending/approved/rejected)
├── applied_on (datetime)
├── reviewed_on (datetime)
└── remarks

BirthCertificate
├── child_name
├── date_of_birth
├── father_name
├── mother_name
├── hospital_name
└── documents (FK → Document)

DeathCertificate
├── deceased_name
├── date_of_death
├── informant_name
├── informant_relation
├── hospital_name
└── documents (FK → Document)

IncomeCertificate
├── annual_income
├── income_source
├── purpose
├── employee_name
└── documents (FK → Document)

TaxPayment
├── property_id
├── tax_type (water/house)
├── financial_year
├── amount
├── late_fee
├── status (pending/paid)
├── receipt_number
└── paid_on (datetime)
```

### URLs
```
/services/                          # List all services
/services/birth-certificate/        # Show birth cert form
/services/death-certificate/        # Show death cert form
/services/income-certificate/       # Show income cert form
/services/certificates/             # List all certificates
/services/certificates/123/         # View certificate detail
/services/certificates/123/download/ # Download PDF
/services/track/ABC123/             # Track application by ID
/services/tax/pay/                  # Pay tax form
/services/tax/history/              # View tax payment history
```

### Views
```
ServicesListView.get()
→ Show available services (birth/death/income certs, tax)

BirthCertificateCreateView.get()  → Show birth cert form
BirthCertificateCreateView.post() → Save application, send PDF

CertificateListView.get()
→ Show user's all applications

CertificateDetailView.get()
→ Show single certificate details

CertificateDownloadView.get()
→ Generate & download PDF

TrackApplicationView.get()
→ Show application status with history

TaxPaymentView.get()  → Show tax payment form
TaxPaymentView.post() → Process payment, update status
```

### Forms
```
BirthCertificateForm
├── child_name
├── date_of_birth
├── father_name
├── mother_name
├── hospital_name
└── certificate_file

DeathCertificateForm
├── deceased_name
├── date_of_death
├── informant_name
├── informant_relation
└── documents

TaxPaymentForm
├── property_id
├── tax_type
├── amount
└── payment_method
```

### Templates
```
services/templates/services/
├── services_list.html              (Choose service)
├── birth_certificate_form.html     (Apply for birth)
├── death_certificate_form.html     (Apply for death)
├── income_certificate_form.html    (Apply for income)
├── certificate_list.html           (My applications)
├── certificate_detail.html         (View details)
├── track_application.html          (Track by ID)
├── tax_payment_form.html           (Pay tax)
└── tax_history.html                (Payment history)
```

---

## 3. COMPLAINTS App (Grievance Management)

### Purpose
File, track, and resolve citizen complaints/grievances

### Models
```
Complaint
├── complaint_id (unique)
├── citizen (FK → User)
├── title
├── description
├── category (road/water/health/education)
├── priority (low/medium/high/urgent)
├── status (open/assigned/resolved/closed)
├── photo (file)
├── filed_on (datetime)
├── resolved_on (datetime)
└── resolution (text)

ComplaintCategory
├── name (road, water, health, etc.)
├── description
└── avg_resolution_time

ComplaintStatusHistory
├── complaint (FK → Complaint)
├── old_status
├── new_status
├── changed_by
└── changed_at (datetime)

ComplaintAttachment
├── complaint (FK → Complaint)
├── file_type (image/pdf/doc)
├── file
└── uploaded_on
```

### URLs
```
/complaints/                        # List my complaints
/complaints/create/                 # File new complaint form
/complaints/123/                    # View complaint details
/complaints/123/update/             # Update status (admin)
/complaints/123/resolve/            # Resolve complaint
/complaints/search/                 # Search complaints
/complaints/by-category/road/       # Filter by category
/complaints/stats/                  # Complaint statistics
```

### Views
```
ComplaintListView.get()
→ Show logged-in user's complaints

ComplaintCreateView.get()  → Show complaint form
ComplaintCreateView.post() → Save new complaint

ComplaintDetailView.get()
→ Show single complaint with history

ComplaintUpdateView.get()  → Show update form (admin)
ComplaintUpdateView.post() → Change status (admin only)

ComplaintResolveView.get()  → Show resolve form
ComplaintResolveView.post() → Save resolution

ComplaintSearchView.post()
→ Search by ID, citizen name, category

CategoryComplaintsView.get()
→ Filter complaints by category
```

### Forms
```
ComplaintForm
├── title
├── description
├── category (dropdown)
├── priority (dropdown)
└── photo (file)

ComplaintResolveForm
├── resolution (textarea)
└── notify_citizen (bool)

ComplaintFilterForm
├── category (select)
├── status (select)
├── priority (select)
└── date_range
```

### Templates
```
complaints/templates/complaints/
├── complaint_list.html         (My complaints)
├── complaint_detail.html       (View complaint)
├── complaint_form.html         (File new)
├── complaint_update.html       (Admin: update status)
├── complaint_resolve.html      (Resolve complaint)
├── complaint_search.html       (Search)
└── complaint_stats.html        (Statistics)
```

---

## 4. DASHBOARD App (Admin Panel)

### Purpose
Administrative panel with statistics, user management, reporting

### Models
```
DashboardSetting
├── admin_user (FK → User)
├── theme (light/dark)
├── items_per_page
└── default_view

SystemLog
├── user (CharField)
├── action (login/approval/rejection/etc)
├── timestamp (datetime)
└── details (JSON)

BulkOperationJob
├── job_id
├── operation_type
├── status (pending/running/completed/failed)
├── total_records
├── processed_records
└── started_at, completed_at
```

### URLs
```
/dashboard/                         # Admin home (stats overview)
/dashboard/applications/            # Review applications
/dashboard/applications/123/review/ # Approve/reject app
/dashboard/complaints/              # Manage complaints
/dashboard/users/                   # User management
/dashboard/users/123/ban/           # Ban user
/dashboard/statistics/              # View charts/graphs
/dashboard/reports/                 # Generate reports
/dashboard/reports/monthly/         # Monthly report
/dashboard/audit-logs/              # System logs
/dashboard/bulk-operations/         # Batch processing
```

### Views
```
DashboardView.get()
→ Show main dashboard (stats, quick info)

ApplicationReviewView.get()
→ Show pending applications list

ApplicationReviewDetailView.get()  → Show app details
ApplicationReviewDetailView.post() → Approve/reject

ComplaintManagementView.get()
→ Show all complaints, filter options

ComplaintAssignView.post()
→ Assign to staff member

UserManagementView.get()
→ List all users, search, filter

UserBanView.post()
→ Ban/unban user

StatisticsView.get()
→ Charts: applications, complaints, users over time

ReportGenerationView.get()
→ Show report options

ReportGenerationView.post()
→ Generate & download report (PDF/CSV)

SystemLogsView.get()
→ Show audit trail (who did what, when)

BulkOperationView.get()
→ Show batch job form

BulkOperationView.post()
→ Start bulk operation
```

### Forms
```
ApplicationReviewForm
├── decision (approve/reject)
└── remarks

UserBanForm
├── reason
└── duration

ReportFilterForm
├── report_type
├── date_from
├── date_to
└── format (PDF/CSV/Excel)

BulkOperationForm
├── operation (generate_certs/send_reminders/etc)
├── filters (category, date range, etc)
└── execute_on (date/time)
```

### Templates
```
dashboard/templates/dashboard/
├── dashboard.html              (Main admin panel)
├── applications.html           (Application review)
├── application_detail.html     (Review single app)
├── complaints.html             (Complaint management)
├── users.html                  (User management)
├── statistics.html             (Charts & graphs)
├── reports.html                (Report generator)
├── audit_logs.html             (System audit trail)
└── bulk_operations.html        (Batch processing)
```

---

## Django Commands for Apps

### Create an app
```bash
python manage.py startapp app_name
```

### Make database changes
```bash
python manage.py makemigrations
python manage.py migrate
```

### Run Django development server
```bash
python manage.py runserver
```

### Create superuser (admin)
```bash
python manage.py createsuperuser
```

### Run tests
```bash
python manage.py test                    # All tests
python manage.py test accounts           # Just accounts app
python manage.py test accounts.models    # Just models in accounts
python manage.py test accounts.tests.TestUserRegistration
```

### Django shell (interactive Python with Django models)
```bash
python manage.py shell

# In shell:
from accounts.models import CustomUser
user = CustomUser.objects.create_user(username='john', password='pass')
user.save()
print(user.username)
```

### Manage migrations
```bash
python manage.py showmigrations          # Show all migrations
python manage.py showmigrations accounts # Show accounts migrations
python manage.py migrate                 # Apply all pending
python manage.py migrate accounts        # Apply accounts only
python manage.py migrate accounts zero   # Undo all accounts migrations
python manage.py migrate accounts 0005   # Go back to migration 0005
```

### Check for issues
```bash
python manage.py check                   # Check configuration
python manage.py check --deploy          # Check production readiness
```

### Create fixtures (test data)
```bash
python manage.py dumpdata accounts > accounts_data.json
python manage.py loaddata accounts_data.json
```

---

## URL Routing Map

```
Root (grampanchayat/urls.py)
│
├── /admin/                                  (Django admin)
│   └── Manage models, users, permissions
│
├── /accounts/
│   ├── register/                            (accounts app)
│   ├── login/
│   ├── logout/
│   └── profile/<id>/
│
├── /services/
│   ├── birth-certificate/                  (services app)
│   ├── death-certificate/
│   ├── income-certificate/
│   ├── tax/pay/
│   └── track/<id>/
│
├── /complaints/
│   ├── create/                              (complaints app)
│   ├── <id>/
│   ├── <id>/update/
│   └── <id>/resolve/
│
└── /dashboard/
    ├── applications/                        (dashboard app)
    ├── complaints/
    ├── users/
    └── statistics/
```

---

## File Creation Checklist

Each app needs these files (after startapp):

```
accounts/
  ✓ __init__.py                 (auto-created)
  ✓ models.py                   (auto-created, EDIT IT)
  ✓ views.py                    (auto-created, EDIT IT)
  ✓ admin.py                    (auto-created, EDIT IT)
  ✓ apps.py                     (auto-created)
  ✓ tests.py                    (auto-created, EDIT IT)
  ✓ migrations/                 (auto-created)
  □ urls.py                     (YOU MUST CREATE)
  □ forms.py                    (YOU MUST CREATE)
  □ templates/accounts/         (YOU MUST CREATE)
  □ static/accounts/            (YOU MUST CREATE)
```

---

## Summary

| App | Purpose | Key Files | Models | Views |
|-----|---------|-----------|--------|-------|
| **accounts** | Authentication | models.py, forms.py | CustomUser | Login, Register |
| **services** | Certificates & Tax | models.py, forms.py | BirthCert, TaxPay | Apply, Download |
| **complaints** | Grievances | models.py, forms.py | Complaint | File, Resolve |
| **dashboard** | Admin Panel | models.py, forms.py | SystemLog | Review, Stats |

All 4 apps created at: `d:\portal\grampanchayat_demo\grampanchayat\`

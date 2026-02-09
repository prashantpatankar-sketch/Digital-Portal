# 📚 DIGITAL GRAM PANCHAYAT PORTAL - COMPLETE SETUP GUIDE

## 🎯 PROJECT OVERVIEW

This is a **production-ready** web portal for Gram Panchayat (village council) administration built with Django and MySQL. It provides a comprehensive digital platform for citizens to access government services online.

---

## 📋 TABLE OF CONTENTS

1. [Project Architecture](#project-architecture)
2. [Database Schema](#database-schema)
3. [Installation Steps](#installation-steps)
4. [Database Setup](#database-setup)
5. [Running the Application](#running-the-application)
6. [Admin Setup](#admin-setup)
7. [Features Explanation](#features-explanation)
8. [Security Features](#security-features)
9. [Troubleshooting](#troubleshooting)
10. [Deployment Guide](#deployment-guide)

---

## 🏗️ PROJECT ARCHITECTURE

### Technology Stack

```
Frontend:
- HTML5, CSS3
- Bootstrap 5 (Responsive UI)
- Bootstrap Icons
- JavaScript (minimal, included via Bootstrap)

Backend:
- Django 4.2+ (Python web framework)
- Django ORM (Database abstraction)
- Django Admin Panel
- Crispy Forms (Form rendering)

Database:
- MySQL 8.0+ (Relational database)

PDF Generation:
- ReportLab (Certificate generation)
```

### Project Structure

```
portal/
├── gram_panchayat/          # Main Django project folder
│   ├── __init__.py
│   ├── settings.py          # Configuration file
│   ├── urls.py              # Main URL routing
│   ├── wsgi.py             # WSGI server config
│   └── asgi.py             # ASGI server config
│
├── portal_app/              # Main application
│   ├── models.py            # Database models (8 tables)
│   ├── views.py             # Business logic (30+ views)
│   ├── forms.py             # Form definitions (10 forms)
│   ├── urls.py              # URL routing
│   ├── admin.py             # Admin panel config
│   ├── apps.py              # App configuration
│   └── templates/           # HTML templates
│       └── portal_app/
│           ├── base.html    # Base template
│           ├── home.html    # Homepage
│           ├── login.html   # Login page
│           ├── register.html # Registration
│           ├── services.html # Services page
│           ├── about.html   # About page
│           ├── track_application.html
│           ├── citizen/     # Citizen templates
│           │   ├── dashboard.html
│           │   ├── apply_birth_certificate.html
│           │   ├── apply_death_certificate.html
│           │   ├── apply_income_certificate.html
│           │   ├── pay_tax.html
│           │   ├── file_complaint.html
│           │   ├── my_applications.html
│           │   ├── application_detail.html
│           │   ├── my_complaints.html
│           │   └── complaint_detail.html
│           └── admin/       # Admin templates
│               ├── dashboard.html
│               ├── applications.html
│               ├── review_application.html
│               ├── complaints.html
│               └── update_complaint.html
│
├── static/                  # Static files (CSS, JS, Images)
├── media/                   # User uploaded files
├── manage.py                # Django management script
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
└── README.md               # Project documentation
```

---

## 🗄️ DATABASE SCHEMA

### Entity Relationship Diagram (Conceptual)

```
CustomUser (Extended User Model)
    ↓
    ├─→ Application (1:N) ─→ ApplicationStatusHistory (1:N)
    │       ↓
    │       ├─→ BirthCertificate (1:1)
    │       ├─→ DeathCertificate (1:1)
    │       ├─→ IncomeCertificate (1:1)
    │       └─→ TaxPayment (1:1)
    │
    └─→ Complaint (1:N)
```

### Database Tables (Detailed)

#### 1. **portal_app_customuser** (User Management)
```sql
- id (Primary Key)
- username (Unique)
- password (Hashed)
- email (Unique)
- first_name
- last_name
- role (citizen/admin)
- phone_number (10 digits, Unique)
- aadhar_number (12 digits, Optional)
- date_of_birth
- address (Text)
- village
- taluka
- district
- state
- pincode (6 digits)
- profile_photo (Image upload)
- is_verified (Boolean)
- created_at (Timestamp)
- updated_at (Timestamp)
- is_active, is_staff, is_superuser (Django auth fields)
```

**Purpose**: Stores all user information (both citizens and admins)

---

#### 2. **portal_app_application** (Central Tracking)
```sql
- id (Primary Key)
- application_number (Unique, Auto-generated)
- applicant_id (Foreign Key → CustomUser)
- application_type (birth_certificate, death_certificate, income_certificate, water_tax, house_tax)
- status (pending, under_review, approved, rejected)
- applied_date (Auto timestamp)
- reviewed_date (Nullable)
- reviewed_by_id (Foreign Key → CustomUser, Nullable)
- admin_remarks (Text, Nullable)
```

**Purpose**: Central tracking system for all types of applications

**Indexes**:
- application_number
- status
- applicant_id + status

---

#### 3. **portal_app_birthcertificate**
```sql
- id (Primary Key)
- application_id (OneToOne → Application)
- child_name
- child_gender (male/female/other)
- date_of_birth
- place_of_birth
- father_name
- father_aadhar (12 digits)
- mother_name
- mother_aadhar (12 digits)
- permanent_address (Text)
- hospital_certificate (File upload)
- parents_id_proof (File upload)
- certificate_number (Unique, Generated after approval)
- issued_date (Nullable)
```

**Purpose**: Birth certificate application details

---

#### 4. **portal_app_deathcertificate**
```sql
- id (Primary Key)
- application_id (OneToOne → Application)
- deceased_name
- deceased_gender
- deceased_age (Integer)
- date_of_death
- place_of_death
- cause_of_death (Text)
- informant_name (Person filing application)
- informant_relation
- informant_phone
- permanent_address (Text)
- hospital_certificate (File upload, Optional)
- deceased_id_proof (File upload)
- certificate_number (Unique, Generated after approval)
- issued_date (Nullable)
```

**Purpose**: Death certificate application details

---

#### 5. **portal_app_incomecertificate**
```sql
- id (Primary Key)
- application_id (OneToOne → Application)
- applicant_name
- father_husband_name
- occupation
- annual_income (Decimal)
- income_source (agriculture/business/salary/pension/other)
- income_details (Text)
- purpose_of_certificate (Text)
- residential_address (Text)
- income_proof (File upload)
- id_proof (File upload)
- ration_card (File upload, Optional)
- certificate_number (Unique, Generated after approval)
- issued_date (Nullable)
- valid_until (Nullable)
```

**Purpose**: Income certificate application details

---

#### 6. **portal_app_taxpayment**
```sql
- id (Primary Key)
- application_id (OneToOne → Application)
- tax_type (water_tax/house_tax)
- property_number
- property_address (Text)
- property_area_sqft (Decimal)
- financial_year (e.g., 2025-26)
- tax_amount (Decimal)
- late_fee (Decimal, Default: 0)
- total_amount (Auto-calculated)
- payment_status (pending/paid/overdue)
- payment_method (online/cash/cheque/dd)
- payment_date (Nullable)
- transaction_id (Optional)
- receipt_number (Unique, Generated after payment)
- property_document (File upload, Optional)
```

**Purpose**: Tax payment records (Water & House tax)

**Indexes**:
- property_number
- payment_status

---

#### 7. **portal_app_complaint**
```sql
- id (Primary Key)
- complaint_number (Unique, Auto-generated)
- complainant_id (Foreign Key → CustomUser)
- category (water_supply/electricity/road/sanitation/street_light/drainage/waste_management/other)
- subject
- description (Text)
- location (Text)
- priority (low/medium/high/urgent)
- status (open/in_progress/resolved/closed)
- complaint_photo (Image upload, Optional)
- filed_date (Auto timestamp)
- assigned_to_id (Foreign Key → CustomUser, Nullable)
- resolved_date (Nullable)
- resolution_remarks (Text, Nullable)
```

**Purpose**: Complaint/Grievance management

**Indexes**:
- complaint_number
- status
- complainant_id + status

---

#### 8. **portal_app_applicationstatushistory** (Audit Trail)
```sql
- id (Primary Key)
- application_id (Foreign Key → Application)
- old_status
- new_status
- changed_by_id (Foreign Key → CustomUser)
- changed_at (Auto timestamp)
- remarks (Text, Nullable)
```

**Purpose**: Maintains complete audit trail of all status changes

---

## 🚀 INSTALLATION STEPS

### Prerequisites

Before starting, ensure you have:

1. **Python 3.8+** installed
   ```powershell
   python --version
   ```

2. **MySQL 8.0+** installed and running
   ```powershell
   mysql --version
   ```

3. **pip** (Python package manager)
   ```powershell
   pip --version
   ```

---

### Step 1: Navigate to Project Directory

```powershell
cd d:\portal
```

---

### Step 2: Create Virtual Environment

**What is a virtual environment?**
- Isolated Python environment for the project
- Prevents conflicts with other Python projects
- Keeps dependencies organized

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# You should see (venv) in your prompt
```

**Deactivate when needed:**
```powershell
deactivate
```

---

### Step 3: Install Python Dependencies

```powershell
# Make sure virtual environment is activated
pip install -r requirements.txt
```

**What gets installed:**
- Django 4.2.9 (Web framework)
- mysqlclient 2.2.1 (MySQL connector)
- Pillow 10.1.0 (Image handling)
- python-decouple 3.8 (Environment variables)
- django-crispy-forms 2.1 (Form rendering)
- crispy-bootstrap5 2.0.0 (Bootstrap 5 support)
- reportlab 4.0.9 (PDF generation)

---

## 🗄️ DATABASE SETUP

### Step 1: Start MySQL Server

Ensure MySQL server is running on your system.

### Step 2: Login to MySQL

```powershell
mysql -u root -p
# Enter your MySQL root password
```

---

### Step 3: Create Database

```sql
-- Create database with UTF-8 encoding
CREATE DATABASE gram_panchayat_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Verify database creation
SHOW DATABASES;

-- Exit MySQL
EXIT;
```

**Database Details:**
- **Name**: `gram_panchayat_db`
- **Character Set**: UTF-8 (for multilingual support)
- **Collation**: Unicode (for proper sorting)

---

### Step 4: Configure Environment Variables

1. **Copy the example environment file:**
```powershell
copy .env.example .env
```

2. **Edit `.env` file** with your settings:
```
DB_NAME=gram_panchayat_db
DB_USER=root
DB_PASSWORD=YOUR_MYSQL_PASSWORD_HERE
DB_HOST=localhost
DB_PORT=3306

SECRET_KEY=django-insecure-CHANGE-THIS-TO-SOMETHING-RANDOM
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Important:**
- Replace `YOUR_MYSQL_PASSWORD_HERE` with your actual MySQL password
- For production, generate a new SECRET_KEY (use Django's `get_random_secret_key()`)
- Set `DEBUG=False` in production

---

### Step 5: Create Database Tables (Migration)

```powershell
# Navigate to project directory (where manage.py is)
cd gram_panchayat

# Create migration files
python manage.py makemigrations

# Apply migrations to database
python manage.py migrate
```

**What happens:**
- Django creates all 8 database tables
- Sets up indexes and foreign key relationships
- Creates Django's built-in tables (auth, sessions, etc.)

**Expected Output:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, portal_app, sessions
Running migrations:
  Applying portal_app.0001_initial... OK
  ...
```

---

## ▶️ RUNNING THE APPLICATION

### Step 1: Create Superuser (Admin Account)

```powershell
python manage.py createsuperuser
```

**Enter the following:**
- Username: `admin` (or your choice)
- Email: `admin@grampanchayat.gov.in`
- Password: (minimum 8 characters, not too common)
- Password (again): (same as above)

**This admin can:**
- Access Django admin panel
- Approve/reject applications
- Manage all users and data

---

### Step 2: Start Development Server

```powershell
python manage.py runserver
```

**Server will start on:** http://127.0.0.1:8000/

**Access points:**
- Homepage: http://127.0.0.1:8000/
- Admin Panel: http://127.0.0.1:8000/admin/
- Citizen Login: http://127.0.0.1:8000/login/
- Registration: http://127.0.0.1:8000/register/

---

## 👨‍💼 ADMIN SETUP

### 1. Login to Django Admin Panel

URL: http://127.0.0.1:8000/admin/

Credentials: (created in Step 1 above)

---

### 2. Create Additional Admin Users

**Option A: Via Django Admin Panel**
1. Login to admin panel
2. Click "Users" → "Add User"
3. Fill in details
4. Check "Staff status" and "Superuser status"
5. Save

**Option B: Via Command**
```powershell
python manage.py createsuperuser
```

---

### 3. Admin Capabilities

From the admin panel, you can:

1. **Manage Users**
   - View all registered citizens
   - Verify user accounts
   - Edit user details
   - Deactivate users if needed

2. **Manage Applications**
   - View all applications
   - Filter by type and status
   - Update application status
   - Add admin remarks

3. **Manage Certificates**
   - View certificate details
   - Generate certificate numbers
   - Set issued dates

4. **Manage Complaints**
   - View all complaints
   - Assign complaints to staff
   - Update status and priority
   - Add resolution remarks

5. **View Statistics**
   - Total users, applications, complaints
   - Status-wise distribution
   - Date-wise reports

---

## 🎯 FEATURES EXPLANATION

### For Citizens

#### 1. **Registration & Login**
- **URL**: `/register/` and `/login/`
- **Fields**: Username, Name, Email, Phone, Aadhar, Address
- **Validation**: Phone (10 digits), Aadhar (12 digits), Pincode (6 digits)
- **Security**: Password hashed using PBKDF2

#### 2. **Dashboard**
- **URL**: `/dashboard/`
- **Shows**:
  - Statistics (Total, Pending, Approved, Rejected)
  - Recent 5 applications
  - Recent 5 complaints
  - Quick action buttons

#### 3. **Birth Certificate Application**
- **URL**: `/apply/birth-certificate/`
- **Documents Required**:
  - Hospital certificate (PDF/Image)
  - Parents ID proof (PDF/Image)
- **Details Collected**:
  - Child: Name, Gender, DOB, Place of birth
  - Parents: Names, Aadhar numbers
  - Address information

#### 4. **Death Certificate Application**
- **URL**: `/apply/death-certificate/`
- **Documents Required**:
  - Hospital/Doctor certificate
  - Deceased person's ID proof
- **Details Collected**:
  - Deceased: Name, Gender, Age, DOB, Cause
  - Informant: Name, Relation, Contact
  - Place and address details

#### 5. **Income Certificate Application**
- **URL**: `/apply/income-certificate/`
- **Documents Required**:
  - Income proof (Salary slip, Form 16, etc.)
  - ID proof (Aadhar, PAN)
  - Ration card (optional)
- **Details Collected**:
  - Personal: Name, Father/Husband name, Occupation
  - Income: Amount, Source, Details
  - Purpose of certificate

#### 6. **Tax Payment**
- **URL**: `/pay-tax/`
- **Types**: Water Tax, House Tax
- **Details Required**:
  - Property number and address
  - Property area (sq ft)
  - Financial year
  - Tax amount
- **Payment Methods**: Online, Cash, Cheque, DD

#### 7. **File Complaint**
- **URL**: `/file-complaint/`
- **Categories**: 
  - Water Supply, Electricity
  - Road & Infrastructure
  - Sanitation, Drainage
  - Street Light, Waste Management
- **Features**:
  - Photo upload (optional)
  - Priority selection
  - Location details

#### 8. **Track Application**
- **URL**: `/track/`
- **Public Access**: Anyone can track with application number
- **Shows**: Status, dates, admin remarks

#### 9. **Download Certificate**
- **URL**: `/download-certificate/<id>/`
- **Format**: PDF
- **Content**: Government-styled certificate with:
  - Certificate number
  - Issued date
  - All application details
  - Official seal (in production)

---

### For Admins

#### 1. **Admin Dashboard**
- **URL**: `/admin-dashboard/`
- **Statistics**:
  - Total citizens
  - Total applications (by status)
  - Total complaints
  - Today's approvals
- **Quick View**:
  - 10 Pending applications
  - 10 Recent complaints

#### 2. **Manage Applications**
- **URL**: `/admin/applications/`
- **Features**:
  - Filter by status and type
  - Pagination (20 per page)
  - Review button for each application

#### 3. **Review Application**
- **URL**: `/admin/application/<id>/review/`
- **Actions**:
  - View all application details
  - View uploaded documents
  - Change status (Pending → Under Review → Approved/Rejected)
  - Add admin remarks
  - Auto-generate certificate number on approval

#### 4. **Manage Complaints**
- **URL**: `/admin/complaints/`
- **Features**:
  - Filter by status and category
  - Update priority
  - Assign to staff members
  - Track resolution

#### 5. **Update Complaint**
- **URL**: `/admin/complaint/<id>/update/`
- **Actions**:
  - Change status
  - Update priority
  - Assign to admin user
  - Add resolution remarks
  - Set resolved date

---

## 🔒 SECURITY FEATURES

### 1. **Authentication & Authorization**
- Password hashing using PBKDF2 algorithm
- Session-based authentication
- CSRF protection on all forms
- Role-based access control (citizen vs admin)

### 2. **Input Validation**
- Phone number: 10 digits, starts with 6-9
- Aadhar: Exactly 12 digits
- Pincode: Exactly 6 digits
- Email: Valid email format
- Form validation on both client and server side

### 3. **SQL Injection Prevention**
- Django ORM parameterizes all queries
- No raw SQL queries used

### 4. **XSS Protection**
- Django auto-escapes all template variables
- CSRF tokens on all forms

### 5. **File Upload Security**
- File type validation
- Accepted formats: PDF, JPG, JPEG, PNG
- Files stored in isolated media directory

### 6. **Session Security**
- Session timeout: 1 hour
- Secure cookies in production
- HTTPS enforcement in production

---

## 🐛 TROUBLESHOOTING

### Issue 1: MySQL Connection Error

**Error:**
```
django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")
```

**Solution:**
1. Check if MySQL service is running
2. Verify `.env` file has correct credentials
3. Test MySQL connection:
   ```powershell
   mysql -u root -p
   ```

---

### Issue 2: Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'django'
```

**Solution:**
1. Ensure virtual environment is activated
   ```powershell
   venv\Scripts\activate
   ```
2. Install requirements again
   ```powershell
   pip install -r requirements.txt
   ```

---

### Issue 3: Migration Errors

**Error:**
```
django.db.migrations.exceptions.InconsistentMigrationHistory
```

**Solution:**
1. Delete all migration files except `__init__.py` in `portal_app/migrations/`
2. Delete database and recreate:
   ```sql
   DROP DATABASE gram_panchayat_db;
   CREATE DATABASE gram_panchayat_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. Run migrations again:
   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

---

### Issue 4: Static Files Not Loading

**Error:** CSS/JS not loading on pages

**Solution:**
1. Run collectstatic:
   ```powershell
   python manage.py collectstatic
   ```
2. Ensure `DEBUG=True` in development
3. Check `STATIC_URL` in settings.py

---

### Issue 5: File Upload Fails

**Error:** Files not uploading

**Solution:**
1. Create media directory:
   ```powershell
   mkdir media
   ```
2. Check `MEDIA_ROOT` and `MEDIA_URL` in settings.py
3. Ensure form has `enctype="multipart/form-data"`

---

## 🌐 DEPLOYMENT GUIDE

### For Production Deployment

#### 1. Update Settings

**settings.py changes:**
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
```

**Security settings:**
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
```

---

#### 2. Collect Static Files

```powershell
python manage.py collectstatic
```

---

#### 3. Database Backup

```powershell
# Backup database
mysqldump -u root -p gram_panchayat_db > backup.sql

# Restore database
mysql -u root -p gram_panchayat_db < backup.sql
```

---

#### 4. Web Server Setup

**Option A: Using Gunicorn + Nginx**

1. Install Gunicorn:
   ```powershell
   pip install gunicorn
   ```

2. Run Gunicorn:
   ```powershell
   gunicorn gram_panchayat.wsgi:application --bind 0.0.0.0:8000
   ```

3. Configure Nginx as reverse proxy

**Option B: Using Apache + mod_wsgi**

1. Install mod_wsgi
2. Configure Apache virtual host
3. Point to wsgi.py file

---

#### 5. SSL Certificate

Use Let's Encrypt for free SSL:
```bash
certbot --nginx -d yourdomain.com
```

---

## 📞 SUPPORT

For issues or questions:
- Check README.md
- Review this SETUP_GUIDE.md
- Check Django documentation: https://docs.djangoproject.com/

---

## ✅ CHECKLIST

Before considering setup complete:

- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] MySQL database created
- [ ] .env file configured correctly
- [ ] Migrations applied successfully
- [ ] Superuser created
- [ ] Development server running
- [ ] Can access homepage
- [ ] Can access admin panel
- [ ] Can register new citizen
- [ ] Can submit an application
- [ ] Admin can review application
- [ ] Can download approved certificate

---

## 🎉 YOU'RE ALL SET!

Your Digital Gram Panchayat Portal is now ready to use!

**Next Steps:**
1. Create test citizen accounts
2. Submit sample applications
3. Test admin approval workflow
4. Customize templates as needed
5. Add your Panchayat's logo and details
6. Configure email notifications (optional)
7. Set up automatic backups

---

**Last Updated:** February 2026
**Version:** 1.0.0
**Developed for:** Digital India Initiative

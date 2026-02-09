# 🗄️ MySQL Database Design - Digital Gram Panchayat Portal

## 📋 Table of Contents
1. [Database Overview](#database-overview)
2. [Entity Relationship Diagram](#entity-relationship-diagram)
3. [Table Schemas](#table-schemas)
4. [Relationships](#relationships)
5. [Indexes & Performance](#indexes--performance)
6. [Migration Commands](#migration-commands)
7. [Sample Data](#sample-data)

---

## Database Overview

**Database Name**: `gram_panchayat_db`  
**Engine**: MySQL 8.0+ / SQLite (development)  
**Character Set**: utf8mb4  
**Collation**: utf8mb4_unicode_ci  
**Total Tables**: 9 core tables

### Core Tables
1. **portal_app_customuser** - User management (Citizens, Staff, Admin)
2. **portal_app_application** - Central application tracking
3. **portal_app_birthcertificate** - Birth certificate details
4. **portal_app_deathcertificate** - Death certificate details
5. **portal_app_incomecertificate** - Income certificate details
6. **portal_app_taxpayment** - Tax payment records
7. **portal_app_complaint** - Complaint/grievance management
8. **portal_app_applicationstatushistory** - Audit trail
9. **django_session** - Session management

---

## Entity Relationship Diagram

```
┌─────────────────────┐
│   CUSTOMUSER        │
│  (Extended User)    │
├─────────────────────┤
│ PK id               │
│    username         │
│    email            │
│    password         │
│    role             │◄─────┐
│    phone_number     │      │
│    aadhar_number    │      │
│    address          │      │
│    village          │      │
│    created_at       │      │
└──────┬──────────────┘      │
       │                      │
       │ 1:N                  │
       │                      │
       ▼                      │
┌─────────────────────┐      │
│   APPLICATION       │      │
│  (Central Tracker)  │      │
├─────────────────────┤      │
│ PK id               │      │
│ UK application_no   │      │
│ FK applicant_id     │──────┘
│ FK reviewed_by_id   │──────┐
│    type             │      │
│    status           │      │
│    applied_date     │      │
│    reviewed_date    │      │
│    admin_remarks    │      │
└──────┬──────────────┘      │
       │ 1:1                 │
       │                      │
   ┌───┴───┬────────┬────────┤
   │       │        │        │
   ▼       ▼        ▼        ▼
┌────┐  ┌────┐  ┌────┐  ┌────┐
│Birth│ │Death│ │Income│ │Tax │
│Cert │ │Cert │ │ Cert │ │Pay │
└────┘  └────┘  └────┘  └────┘


┌─────────────────────┐
│   COMPLAINT         │
├─────────────────────┤
│ PK id               │
│ UK complaint_no     │
│ FK complainant_id   │──────┐
│ FK assigned_to_id   │──────┤
│    category         │      │
│    subject          │      │
│    description      │      │
│    status           │      │
│    priority         │      │
│    filed_date       │      │
└─────────────────────┘      │
                              │
                              │
┌─────────────────────┐      │
│  STATUS_HISTORY     │      │
│   (Audit Trail)     │      │
├─────────────────────┤      │
│ PK id               │      │
│ FK application_id   │      │
│ FK changed_by_id    │──────┘
│    old_status       │
│    new_status       │
│    changed_at       │
│    remarks          │
└─────────────────────┘
```

---

## Table Schemas

### 1. CustomUser Table

**Table**: `portal_app_customuser`  
**Inherits**: Django's `auth_user` table  
**Purpose**: User authentication and profile management

```sql
CREATE TABLE portal_app_customuser (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    password VARCHAR(128) NOT NULL,
    last_login DATETIME(6) NULL,
    is_superuser TINYINT(1) NOT NULL,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    is_staff TINYINT(1) NOT NULL,
    is_active TINYINT(1) NOT NULL,
    date_joined DATETIME(6) NOT NULL,
    
    -- Custom Fields
    role VARCHAR(20) NOT NULL DEFAULT 'citizen',
    phone_number VARCHAR(10) UNIQUE NOT NULL,
    aadhar_number VARCHAR(12) UNIQUE NULL,
    date_of_birth DATE NULL,
    address TEXT NOT NULL,
    village VARCHAR(100) NOT NULL DEFAULT 'Model Village',
    taluka VARCHAR(100) NOT NULL DEFAULT 'Model Taluka',
    district VARCHAR(100) NOT NULL DEFAULT 'Model District',
    state VARCHAR(100) NOT NULL DEFAULT 'Maharashtra',
    pincode VARCHAR(6) NOT NULL,
    profile_photo VARCHAR(100) NULL,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    is_verified TINYINT(1) NOT NULL DEFAULT 0,
    
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_phone (phone_number),
    INDEX idx_role (role),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Constraints**:
- Phone: 10 digits, starts with 6-9
- Aadhar: 12 digits (optional)
- Pincode: 6 digits
- Role: 'citizen', 'staff', or 'admin'

---

### 2. Application Table

**Table**: `portal_app_application`  
**Purpose**: Central tracking for all application types

```sql
CREATE TABLE portal_app_application (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    application_number VARCHAR(20) UNIQUE NOT NULL,
    applicant_id BIGINT NOT NULL,
    reviewed_by_id BIGINT NULL,
    application_type VARCHAR(20) NOT NULL,
    status VARCHAR(15) NOT NULL DEFAULT 'pending',
    applied_date DATETIME(6) NOT NULL,
    reviewed_date DATETIME(6) NULL,
    admin_remarks TEXT NULL,
    
    FOREIGN KEY (applicant_id) 
        REFERENCES portal_app_customuser(id) 
        ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by_id) 
        REFERENCES portal_app_customuser(id) 
        ON DELETE SET NULL,
    
    INDEX idx_app_number (application_number),
    INDEX idx_status (status),
    INDEX idx_applicant_status (applicant_id, status),
    INDEX idx_type (application_type),
    INDEX idx_applied_date (applied_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Application Types**:
- `birth_certificate`
- `death_certificate`
- `income_certificate`
- `water_tax`
- `house_tax`

**Status Flow**:
```
pending → under_review → approved/rejected
```

**Application Number Format**: `GP{TYPE}{TIMESTAMP}`
- Example: `GPBIRT20260206143052`

---

### 3. BirthCertificate Table

**Table**: `portal_app_birthcertificate`  
**Purpose**: Birth certificate application details

```sql
CREATE TABLE portal_app_birthcertificate (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    application_id BIGINT UNIQUE NOT NULL,
    
    -- Child Information
    child_name VARCHAR(200) NOT NULL,
    child_gender VARCHAR(10) NOT NULL,
    date_of_birth DATE NOT NULL,
    place_of_birth VARCHAR(200) NOT NULL,
    
    -- Parent Information
    father_name VARCHAR(200) NOT NULL,
    father_aadhar VARCHAR(12) NULL,
    mother_name VARCHAR(200) NOT NULL,
    mother_aadhar VARCHAR(12) NULL,
    
    -- Address
    permanent_address TEXT NOT NULL,
    
    -- Documents (File paths)
    hospital_certificate VARCHAR(100) NOT NULL,
    parents_id_proof VARCHAR(100) NOT NULL,
    
    -- Certificate Details (After Approval)
    certificate_number VARCHAR(50) UNIQUE NULL,
    issued_date DATE NULL,
    
    FOREIGN KEY (application_id) 
        REFERENCES portal_app_application(id) 
        ON DELETE CASCADE,
    
    INDEX idx_child_name (child_name),
    INDEX idx_cert_number (certificate_number),
    INDEX idx_dob (date_of_birth)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**File Upload Paths**:
- Hospital Certificate: `media/birth_certificates/hospital/`
- Parents ID: `media/birth_certificates/id_proof/`

---

### 4. DeathCertificate Table

**Table**: `portal_app_deathcertificate`  
**Purpose**: Death certificate application details

```sql
CREATE TABLE portal_app_deathcertificate (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    application_id BIGINT UNIQUE NOT NULL,
    
    -- Deceased Information
    deceased_name VARCHAR(200) NOT NULL,
    deceased_gender VARCHAR(10) NOT NULL,
    deceased_age INT NOT NULL,
    date_of_death DATE NOT NULL,
    place_of_death VARCHAR(200) NOT NULL,
    cause_of_death TEXT NOT NULL,
    
    -- Informant (Applicant)
    informant_name VARCHAR(200) NOT NULL,
    informant_relation VARCHAR(100) NOT NULL,
    informant_phone VARCHAR(10) NOT NULL,
    
    -- Address
    permanent_address TEXT NOT NULL,
    
    -- Documents
    hospital_certificate VARCHAR(100) NULL,
    deceased_id_proof VARCHAR(100) NOT NULL,
    
    -- Certificate Details
    certificate_number VARCHAR(50) UNIQUE NULL,
    issued_date DATE NULL,
    
    FOREIGN KEY (application_id) 
        REFERENCES portal_app_application(id) 
        ON DELETE CASCADE,
    
    INDEX idx_deceased_name (deceased_name),
    INDEX idx_cert_number (certificate_number),
    INDEX idx_dod (date_of_death)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

### 5. IncomeCertificate Table

**Table**: `portal_app_incomecertificate`  
**Purpose**: Income certificate application details

```sql
CREATE TABLE portal_app_incomecertificate (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    application_id BIGINT UNIQUE NOT NULL,
    
    -- Applicant Information
    applicant_name VARCHAR(200) NOT NULL,
    father_husband_name VARCHAR(200) NOT NULL,
    occupation VARCHAR(200) NOT NULL,
    
    -- Income Details
    annual_income DECIMAL(10, 2) NOT NULL,
    income_source VARCHAR(20) NOT NULL,
    income_details TEXT NOT NULL,
    
    -- Purpose
    purpose_of_certificate TEXT NOT NULL,
    
    -- Address
    residential_address TEXT NOT NULL,
    
    -- Documents
    income_proof VARCHAR(100) NOT NULL,
    id_proof VARCHAR(100) NOT NULL,
    ration_card VARCHAR(100) NULL,
    
    -- Certificate Details
    certificate_number VARCHAR(50) UNIQUE NULL,
    issued_date DATE NULL,
    valid_until DATE NULL,
    
    FOREIGN KEY (application_id) 
        REFERENCES portal_app_application(id) 
        ON DELETE CASCADE,
    
    INDEX idx_applicant_name (applicant_name),
    INDEX idx_cert_number (certificate_number),
    INDEX idx_income (annual_income)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Income Sources**:
- agriculture
- business
- salary
- pension
- other

---

### 6. TaxPayment Table

**Table**: `portal_app_taxpayment`  
**Purpose**: Water tax and house tax payments

```sql
CREATE TABLE portal_app_taxpayment (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    application_id BIGINT UNIQUE NOT NULL,
    
    -- Tax Details
    tax_type VARCHAR(15) NOT NULL,
    
    -- Property Details
    property_number VARCHAR(50) NOT NULL,
    property_address TEXT NOT NULL,
    property_area_sqft DECIMAL(10, 2) NOT NULL,
    
    -- Financial Year
    financial_year VARCHAR(10) NOT NULL,
    
    -- Tax Calculation
    tax_amount DECIMAL(10, 2) NOT NULL,
    late_fee DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    total_amount DECIMAL(10, 2) NOT NULL,
    
    -- Payment Details
    payment_status VARCHAR(10) NOT NULL DEFAULT 'pending',
    payment_method VARCHAR(10) NULL,
    payment_date DATETIME(6) NULL,
    transaction_id VARCHAR(100) NULL,
    receipt_number VARCHAR(50) UNIQUE NULL,
    
    -- Documents
    property_document VARCHAR(100) NULL,
    
    FOREIGN KEY (application_id) 
        REFERENCES portal_app_application(id) 
        ON DELETE CASCADE,
    
    INDEX idx_property_number (property_number),
    INDEX idx_payment_status (payment_status),
    INDEX idx_financial_year (financial_year),
    INDEX idx_receipt_number (receipt_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Tax Types**:
- `water_tax`
- `house_tax`

**Payment Status**:
- `pending` → `paid` / `overdue`

**Receipt Number Format**: `RCP{TIMESTAMP}`

---

### 7. Complaint Table

**Table**: `portal_app_complaint`  
**Purpose**: Complaint/grievance management system

```sql
CREATE TABLE portal_app_complaint (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    complaint_number VARCHAR(20) UNIQUE NOT NULL,
    complainant_id BIGINT NOT NULL,
    assigned_to_id BIGINT NULL,
    
    -- Complaint Details
    category VARCHAR(20) NOT NULL,
    subject VARCHAR(300) NOT NULL,
    description TEXT NOT NULL,
    location TEXT NOT NULL,
    
    -- Priority & Status
    priority VARCHAR(10) NOT NULL DEFAULT 'medium',
    status VARCHAR(15) NOT NULL DEFAULT 'open',
    
    -- Attachments
    complaint_photo VARCHAR(100) NULL,
    
    -- Tracking
    filed_date DATETIME(6) NOT NULL,
    resolved_date DATETIME(6) NULL,
    
    -- Resolution
    resolution_remarks TEXT NULL,
    
    FOREIGN KEY (complainant_id) 
        REFERENCES portal_app_customuser(id) 
        ON DELETE CASCADE,
    FOREIGN KEY (assigned_to_id) 
        REFERENCES portal_app_customuser(id) 
        ON DELETE SET NULL,
    
    INDEX idx_complaint_number (complaint_number),
    INDEX idx_status (status),
    INDEX idx_complainant_status (complainant_id, status),
    INDEX idx_category (category),
    INDEX idx_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Categories**:
- water_supply
- electricity
- road
- sanitation
- street_light
- drainage
- waste_management
- other

**Priority Levels**:
```
low → medium → high → urgent
```

**Status Flow**:
```
open → in_progress → resolved → closed
```

**Complaint Number Format**: `CMP{TIMESTAMP}`

---

### 8. ApplicationStatusHistory Table

**Table**: `portal_app_applicationstatushistory`  
**Purpose**: Audit trail for application status changes

```sql
CREATE TABLE portal_app_applicationstatushistory (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    application_id BIGINT NOT NULL,
    changed_by_id BIGINT NULL,
    
    old_status VARCHAR(15) NOT NULL,
    new_status VARCHAR(15) NOT NULL,
    changed_at DATETIME(6) NOT NULL,
    remarks TEXT NULL,
    
    FOREIGN KEY (application_id) 
        REFERENCES portal_app_application(id) 
        ON DELETE CASCADE,
    FOREIGN KEY (changed_by_id) 
        REFERENCES portal_app_customuser(id) 
        ON DELETE SET NULL,
    
    INDEX idx_application_id (application_id),
    INDEX idx_changed_at (changed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Tracks**:
- Who changed the status
- When it was changed
- From what to what
- Admin remarks

---

## Relationships

### One-to-Many Relationships

1. **CustomUser → Application**
   - One user can have many applications
   - FK: `application.applicant_id → customuser.id`
   - Related name: `applications`

2. **CustomUser → Application (Reviewer)**
   - One staff/admin can review many applications
   - FK: `application.reviewed_by_id → customuser.id`
   - Related name: `reviewed_applications`

3. **CustomUser → Complaint**
   - One user can file many complaints
   - FK: `complaint.complainant_id → customuser.id`
   - Related name: `complaints`

4. **CustomUser → Complaint (Assignee)**
   - One staff can be assigned many complaints
   - FK: `complaint.assigned_to_id → customuser.id`
   - Related name: `assigned_complaints`

5. **Application → StatusHistory**
   - One application can have many status changes
   - FK: `statushistory.application_id → application.id`
   - Related name: `status_history`

### One-to-One Relationships

1. **Application ↔ BirthCertificate**
   - FK: `birthcertificate.application_id → application.id`
   - Related name: `birth_certificate`

2. **Application ↔ DeathCertificate**
   - FK: `deathcertificate.application_id → application.id`
   - Related name: `death_certificate`

3. **Application ↔ IncomeCertificate**
   - FK: `incomecertificate.application_id → application.id`
   - Related name: `income_certificate`

4. **Application ↔ TaxPayment**
   - FK: `taxpayment.application_id → application.id`
   - Related name: `tax_payment`

---

## Indexes & Performance

### Primary Indexes (Automatically Created)
- All tables have `PRIMARY KEY (id)`

### Unique Indexes
- `customuser.username`
- `customuser.email`
- `customuser.phone_number`
- `customuser.aadhar_number` (if not NULL)
- `application.application_number`
- `birthcertificate.certificate_number`
- `deathcertificate.certificate_number`
- `incomecertificate.certificate_number`
- `taxpayment.receipt_number`
- `complaint.complaint_number`

### Composite Indexes (for common queries)
```sql
-- Applications by user and status
INDEX idx_applicant_status ON application(applicant_id, status);

-- Complaints by user and status
INDEX idx_complainant_status ON complaint(complainant_id, status);
```

### Performance Optimization Tips

1. **Frequent Queries**:
   ```sql
   -- Get pending applications
   SELECT * FROM application WHERE status = 'pending';
   -- Uses: idx_status
   
   -- Get user's applications
   SELECT * FROM application WHERE applicant_id = 123;
   -- Uses: applicant_id FK index
   
   -- Get user's pending applications
   SELECT * FROM application 
   WHERE applicant_id = 123 AND status = 'pending';
   -- Uses: idx_applicant_status (composite)
   ```

2. **File Fields**: Store only file paths in DB, actual files in media directory

3. **Timestamps**: Use `auto_now_add=True` and `auto_now=True` for automatic tracking

---

## Migration Commands

### 1. Initial Setup

```bash
# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install Django PyMySQL python-decouple

# Configure database (MySQL)
# Edit .env file:
DB_ENGINE=mysql
DB_NAME=gram_panchayat_db
DB_USER=root
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=3306
```

### 2. Create Database (MySQL)

```sql
-- Login to MySQL
mysql -u root -p

-- Create database
CREATE DATABASE gram_panchayat_db 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- Verify
SHOW DATABASES;

-- Exit
EXIT;
```

### 3. Run Django Migrations

```bash
# Create migration files
python manage.py makemigrations

# Expected output:
# Migrations for 'portal_app':
#   portal_app\migrations\0001_initial.py
#     - Create model CustomUser
#     - Create model Application
#     - Create model BirthCertificate
#     - Create model DeathCertificate
#     - Create model IncomeCertificate
#     - Create model TaxPayment
#     - Create model Complaint
#     - Create model ApplicationStatusHistory

# Apply migrations
python manage.py migrate

# Expected output:
# Operations to perform:
#   Apply all migrations: admin, auth, contenttypes, portal_app, sessions
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying contenttypes.0002_remove_content_type_name... OK
#   Applying auth.0001_initial... OK
#   Applying portal_app.0001_initial... OK
#   Applying portal_app.0002_alter_customuser_role... OK
#   ...
```

### 4. Verify Tables

```bash
# Django shell
python manage.py dbshell
```

```sql
-- Show all tables
SHOW TABLES;

-- Describe table structure
DESCRIBE portal_app_customuser;
DESCRIBE portal_app_application;
DESCRIBE portal_app_birthcertificate;
DESCRIBE portal_app_taxpayment;
DESCRIBE portal_app_complaint;

-- Show indexes
SHOW INDEX FROM portal_app_application;
SHOW INDEX FROM portal_app_complaint;

-- Exit
EXIT;
```

### 5. Create Superuser

```bash
python manage.py createsuperuser

# Follow prompts:
# Username: admin
# Email: admin@grampanchayat.gov.in
# Password: ********
# Password (again): ********
```

---

## Sample Data

### Insert Sample Users

```python
# Django shell
python manage.py shell
```

```python
from portal_app.models import CustomUser
from django.utils import timezone

# Create Admin
admin = CustomUser.objects.create_user(
    username='admin',
    password='Admin@1234',
    email='admin@grampanchayat.gov.in',
    first_name='System',
    last_name='Administrator',
    role='admin',
    phone_number='9876543210',
    address='Gram Panchayat Office',
    village='Model Village',
    pincode='123456',
    is_staff=True,
    is_active=True
)

# Create Staff
staff = CustomUser.objects.create_user(
    username='staff1',
    password='Staff@1234',
    email='staff@grampanchayat.gov.in',
    first_name='Priya',
    last_name='Sharma',
    role='staff',
    phone_number='9876543211',
    address='Panchayat Building',
    village='Model Village',
    pincode='123456',
    is_active=True
)

# Create Citizens
citizen1 = CustomUser.objects.create_user(
    username='ramesh',
    password='Ramesh@1234',
    email='ramesh@example.com',
    first_name='Ramesh',
    last_name='Kumar',
    role='citizen',
    phone_number='9876543212',
    aadhar_number='123456789012',
    date_of_birth='1990-01-15',
    address='123 Main Street',
    village='Model Village',
    pincode='123456',
    is_active=True
)

citizen2 = CustomUser.objects.create_user(
    username='sunita',
    password='Sunita@1234',
    email='sunita@example.com',
    first_name='Sunita',
    last_name='Devi',
    role='citizen',
    phone_number='9876543213',
    aadhar_number='123456789013',
    date_of_birth='1985-05-20',
    address='456 Village Road',
    village='Model Village',
    pincode='123456',
    is_active=True
)

print("✅ Sample users created!")
```

### Insert Sample Application

```python
from portal_app.models import Application, BirthCertificate
from datetime import date

# Create Birth Certificate Application
app = Application.objects.create(
    applicant=citizen1,
    application_type='birth_certificate',
    status='pending'
)

birth_cert = BirthCertificate.objects.create(
    application=app,
    child_name='Baby Kumar',
    child_gender='male',
    date_of_birth=date(2025, 1, 15),
    place_of_birth='District Hospital',
    father_name='Ramesh Kumar',
    father_aadhar='123456789012',
    mother_name='Sunita Devi',
    mother_aadhar='123456789013',
    permanent_address='123 Main Street, Model Village'
)

print(f"✅ Application created: {app.application_number}")
```

### Insert Sample Complaint

```python
from portal_app.models import Complaint

complaint = Complaint.objects.create(
    complainant=citizen2,
    category='water_supply',
    subject='No water supply in area',
    description='Water supply has been disrupted for 3 days in our locality.',
    location='Sector 5, Model Village',
    priority='high',
    status='open'
)

print(f"✅ Complaint filed: {complaint.complaint_number}")
```

---

## Database Queries

### Common Queries

```python
# Get all pending applications
pending_apps = Application.objects.filter(status='pending')

# Get user's applications
user_apps = Application.objects.filter(applicant=citizen1)

# Get birth certificates
birth_certs = BirthCertificate.objects.select_related('application').all()

# Get applications with status history
apps_with_history = Application.objects.prefetch_related('status_history').all()

# Get open complaints assigned to staff
assigned_complaints = Complaint.objects.filter(
    assigned_to=staff,
    status='open'
)

# Get tax payments for financial year
tax_2025 = TaxPayment.objects.filter(
    financial_year='2025-26',
    payment_status='paid'
)

# Statistics
total_users = CustomUser.objects.filter(role='citizen').count()
total_apps = Application.objects.count()
pending_count = Application.objects.filter(status='pending').count()
approved_today = Application.objects.filter(
    status='approved',
    reviewed_date__date=timezone.now().date()
).count()
```

---

## Backup & Restore

### Backup Database

```bash
# MySQL Backup
mysqldump -u root -p gram_panchayat_db > backup_$(date +%Y%m%d).sql

# Django Backup (JSON format)
python manage.py dumpdata > backup_$(date +%Y%m%d).json

# Specific app backup
python manage.py dumpdata portal_app > portal_app_backup.json
```

### Restore Database

```bash
# MySQL Restore
mysql -u root -p gram_panchayat_db < backup_20260206.sql

# Django Restore
python manage.py loaddata backup_20260206.json
```

---

## Performance Monitoring

```sql
-- Show slow queries
SHOW PROCESSLIST;

-- Show table sizes
SELECT 
    table_name AS 'Table',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.TABLES
WHERE table_schema = 'gram_panchayat_db'
ORDER BY (data_length + index_length) DESC;

-- Show index usage
SELECT * FROM sys.schema_unused_indexes 
WHERE object_schema = 'gram_panchayat_db';
```

---

## Summary

✅ **9 Core Tables** designed  
✅ **Proper Relationships** (FK constraints)  
✅ **Optimized Indexes** for performance  
✅ **Validation** at database level  
✅ **Audit Trail** (status history)  
✅ **File Management** (media paths)  
✅ **Auto-generated IDs** (application numbers, receipts)  

**Database Status**: ✅ Production Ready

---

**Created**: February 6, 2026  
**Version**: 1.0  
**Engine**: MySQL 8.0+ / SQLite

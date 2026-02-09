# 🗄️ DATABASE SCHEMA DOCUMENTATION

## Overview

The Digital Gram Panchayat Portal uses **8 main database tables** to manage all operations. This document provides detailed schema information.

---

## Table Relationships Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CUSTOMUSER (Users)                          │
│  - id (PK)                                                          │
│  - username, password, email                                        │
│  - role (citizen/admin)                                             │
│  - phone_number, aadhar_number                                      │
│  - address, village, pincode                                        │
└───────────┬─────────────────────────────────┬─────────────────────┘
            │                                  │
            │ 1:N                             │ 1:N
            │                                  │
    ┌───────▼──────────────────────┐    ┌────▼────────────────────┐
    │    APPLICATION               │    │    COMPLAINT            │
    │  - id (PK)                   │    │  - id (PK)              │
    │  - application_number (UK)   │    │  - complaint_number(UK) │
    │  - applicant_id (FK)         │    │  - complainant_id (FK)  │
    │  - application_type          │    │  - category             │
    │  - status                    │    │  - subject              │
    │  - reviewed_by_id (FK)       │    │  - status               │
    └───┬──────────────────────────┘    │  - priority             │
        │                                └─────────────────────────┘
        │ 1:1 (each)
        │
        ├──────────────────────────────────────┐
        │                                      │
        │                                      │
┌───────▼──────────────────┐    ┌──────────────▼──────────────────┐
│  BIRTHCERTIFICATE        │    │  DEATHCERTIFICATE               │
│  - id (PK)               │    │  - id (PK)                      │
│  - application_id (FK)   │    │  - application_id (FK)          │
│  - child_name            │    │  - deceased_name                │
│  - date_of_birth         │    │  - date_of_death                │
│  - father_name           │    │  - deceased_age                 │
│  - mother_name           │    │  - informant_name               │
│  - certificate_number    │    │  - certificate_number           │
└──────────────────────────┘    └─────────────────────────────────┘
        │                                      │
        │                                      │
┌───────▼──────────────────┐    ┌──────────────▼──────────────────┐
│  INCOMECERTIFICATE       │    │  TAXPAYMENT                     │
│  - id (PK)               │    │  - id (PK)                      │
│  - application_id (FK)   │    │  - application_id (FK)          │
│  - applicant_name        │    │  - tax_type                     │
│  - annual_income         │    │  - property_number              │
│  - income_source         │    │  - tax_amount                   │
│  - occupation            │    │  - payment_status               │
│  - certificate_number    │    │  - receipt_number               │
└──────────────────────────┘    └─────────────────────────────────┘

        ┌──────────────────────────────────────────┐
        │  APPLICATIONSTATUSHISTORY (Audit Trail)  │
        │  - id (PK)                               │
        │  - application_id (FK)                   │
        │  - old_status                            │
        │  - new_status                            │
        │  - changed_by_id (FK)                    │
        │  - changed_at                            │
        └──────────────────────────────────────────┘
```

**Legend:**
- PK = Primary Key
- FK = Foreign Key
- UK = Unique Key
- 1:N = One to Many relationship
- 1:1 = One to One relationship

---

## Table Details

### 1. CustomUser (portal_app_customuser)

**Purpose:** Extended Django user model for both citizens and admins

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInt | PRIMARY KEY | Auto-increment ID |
| username | VARCHAR(150) | UNIQUE, NOT NULL | Login username |
| password | VARCHAR(128) | NOT NULL | Hashed password |
| email | VARCHAR(254) | UNIQUE | Email address |
| first_name | VARCHAR(150) | | First name |
| last_name | VARCHAR(150) | | Last name |
| role | VARCHAR(10) | DEFAULT 'citizen' | citizen or admin |
| phone_number | VARCHAR(10) | UNIQUE, NOT NULL | 10-digit mobile |
| aadhar_number | VARCHAR(12) | UNIQUE, NULLABLE | 12-digit Aadhar |
| date_of_birth | DATE | NULLABLE | Date of birth |
| address | TEXT | NOT NULL | Complete address |
| village | VARCHAR(100) | DEFAULT 'Model Village' | Village name |
| taluka | VARCHAR(100) | DEFAULT 'Model Taluka' | Taluka name |
| district | VARCHAR(100) | DEFAULT 'Model District' | District name |
| state | VARCHAR(100) | DEFAULT 'Maharashtra' | State name |
| pincode | VARCHAR(6) | NOT NULL | 6-digit PIN code |
| profile_photo | VARCHAR(100) | NULLABLE | Image path |
| is_verified | BOOLEAN | DEFAULT FALSE | Account verified |
| created_at | DATETIME | AUTO | Registration date |
| updated_at | DATETIME | AUTO | Last update date |
| is_active | BOOLEAN | DEFAULT TRUE | Account active |
| is_staff | BOOLEAN | DEFAULT FALSE | Staff access |
| is_superuser | BOOLEAN | DEFAULT FALSE | Superuser access |

**Indexes:**
- PRIMARY KEY (id)
- UNIQUE (username)
- UNIQUE (email)
- UNIQUE (phone_number)
- UNIQUE (aadhar_number)
- INDEX (created_at)

---

### 2. Application (portal_app_application)

**Purpose:** Central tracking for all application types

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInt | PRIMARY KEY | Auto-increment ID |
| application_number | VARCHAR(20) | UNIQUE, NOT NULL | Auto-generated (GPxxxx...) |
| applicant_id | BigInt | FOREIGN KEY | → customuser.id |
| application_type | VARCHAR(20) | NOT NULL | Type of application |
| status | VARCHAR(15) | DEFAULT 'pending' | pending/under_review/approved/rejected |
| applied_date | DATETIME | AUTO | Submission timestamp |
| reviewed_date | DATETIME | NULLABLE | Review timestamp |
| reviewed_by_id | BigInt | FOREIGN KEY, NULLABLE | → customuser.id |
| admin_remarks | TEXT | NULLABLE | Admin comments |

**Indexes:**
- PRIMARY KEY (id)
- UNIQUE (application_number)
- INDEX (application_number)
- INDEX (status)
- INDEX (applicant_id, status)
- FOREIGN KEY (applicant_id) → customuser(id) ON DELETE CASCADE
- FOREIGN KEY (reviewed_by_id) → customuser(id) ON DELETE SET NULL

**Application Types:**
- birth_certificate
- death_certificate
- income_certificate
- water_tax
- house_tax

**Status Values:**
- pending (Initial state)
- under_review (Admin is reviewing)
- approved (Approved by admin)
- rejected (Rejected by admin)

---

### 3. BirthCertificate (portal_app_birthcertificate)

**Purpose:** Birth certificate application details

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInt | PRIMARY KEY | Auto-increment ID |
| application_id | BigInt | UNIQUE, FOREIGN KEY | → application.id |
| child_name | VARCHAR(200) | NOT NULL | Child's full name |
| child_gender | VARCHAR(10) | NOT NULL | male/female/other |
| date_of_birth | DATE | NOT NULL | Birth date |
| place_of_birth | VARCHAR(200) | NOT NULL | Birth location |
| father_name | VARCHAR(200) | NOT NULL | Father's name |
| father_aadhar | VARCHAR(12) | NULLABLE | Father's Aadhar |
| mother_name | VARCHAR(200) | NOT NULL | Mother's name |
| mother_aadhar | VARCHAR(12) | NULLABLE | Mother's Aadhar |
| permanent_address | TEXT | NOT NULL | Permanent address |
| hospital_certificate | VARCHAR(100) | NOT NULL | File path |
| parents_id_proof | VARCHAR(100) | NOT NULL | File path |
| certificate_number | VARCHAR(50) | UNIQUE, NULLABLE | Generated on approval |
| issued_date | DATE | NULLABLE | Issue date |

**Indexes:**
- PRIMARY KEY (id)
- UNIQUE (application_id)
- UNIQUE (certificate_number)
- FOREIGN KEY (application_id) → application(id) ON DELETE CASCADE

---

### 4. DeathCertificate (portal_app_deathcertificate)

**Purpose:** Death certificate application details

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInt | PRIMARY KEY | Auto-increment ID |
| application_id | BigInt | UNIQUE, FOREIGN KEY | → application.id |
| deceased_name | VARCHAR(200) | NOT NULL | Deceased person's name |
| deceased_gender | VARCHAR(10) | NOT NULL | male/female/other |
| deceased_age | INT | NOT NULL | Age at death |
| date_of_death | DATE | NOT NULL | Death date |
| place_of_death | VARCHAR(200) | NOT NULL | Death location |
| cause_of_death | TEXT | NOT NULL | Cause description |
| informant_name | VARCHAR(200) | NOT NULL | Person filing |
| informant_relation | VARCHAR(100) | NOT NULL | Relation to deceased |
| informant_phone | VARCHAR(10) | NOT NULL | Contact number |
| permanent_address | TEXT | NOT NULL | Deceased's address |
| hospital_certificate | VARCHAR(100) | NULLABLE | File path |
| deceased_id_proof | VARCHAR(100) | NOT NULL | File path |
| certificate_number | VARCHAR(50) | UNIQUE, NULLABLE | Generated on approval |
| issued_date | DATE | NULLABLE | Issue date |

**Indexes:**
- PRIMARY KEY (id)
- UNIQUE (application_id)
- UNIQUE (certificate_number)
- FOREIGN KEY (application_id) → application(id) ON DELETE CASCADE

---

### 5. IncomeCertificate (portal_app_incomecertificate)

**Purpose:** Income certificate application details

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInt | PRIMARY KEY | Auto-increment ID |
| application_id | BigInt | UNIQUE, FOREIGN KEY | → application.id |
| applicant_name | VARCHAR(200) | NOT NULL | Applicant's name |
| father_husband_name | VARCHAR(200) | NOT NULL | Father/Husband name |
| occupation | VARCHAR(200) | NOT NULL | Occupation |
| annual_income | DECIMAL(10,2) | NOT NULL | Income in ₹ |
| income_source | VARCHAR(20) | NOT NULL | Source type |
| income_details | TEXT | NOT NULL | Detailed description |
| purpose_of_certificate | TEXT | NOT NULL | Why needed |
| residential_address | TEXT | NOT NULL | Address |
| income_proof | VARCHAR(100) | NOT NULL | File path |
| id_proof | VARCHAR(100) | NOT NULL | File path |
| ration_card | VARCHAR(100) | NULLABLE | File path |
| certificate_number | VARCHAR(50) | UNIQUE, NULLABLE | Generated on approval |
| issued_date | DATE | NULLABLE | Issue date |
| valid_until | DATE | NULLABLE | Expiry date |

**Indexes:**
- PRIMARY KEY (id)
- UNIQUE (application_id)
- UNIQUE (certificate_number)
- FOREIGN KEY (application_id) → application(id) ON DELETE CASCADE

**Income Sources:**
- agriculture
- business
- salary
- pension
- other

---

### 6. TaxPayment (portal_app_taxpayment)

**Purpose:** Tax payment records

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInt | PRIMARY KEY | Auto-increment ID |
| application_id | BigInt | UNIQUE, FOREIGN KEY | → application.id |
| tax_type | VARCHAR(15) | NOT NULL | water_tax/house_tax |
| property_number | VARCHAR(50) | NOT NULL | Property ID |
| property_address | TEXT | NOT NULL | Property address |
| property_area_sqft | DECIMAL(10,2) | NOT NULL | Area in sq ft |
| financial_year | VARCHAR(10) | NOT NULL | e.g., 2025-26 |
| tax_amount | DECIMAL(10,2) | NOT NULL | Tax in ₹ |
| late_fee | DECIMAL(10,2) | DEFAULT 0 | Late fee in ₹ |
| total_amount | DECIMAL(10,2) | NOT NULL | Auto-calculated |
| payment_status | VARCHAR(10) | DEFAULT 'pending' | pending/paid/overdue |
| payment_method | VARCHAR(10) | NULLABLE | online/cash/cheque/dd |
| payment_date | DATETIME | NULLABLE | Payment timestamp |
| transaction_id | VARCHAR(100) | NULLABLE | Transaction ID |
| receipt_number | VARCHAR(50) | UNIQUE, NULLABLE | Auto-generated |
| property_document | VARCHAR(100) | NULLABLE | File path |

**Indexes:**
- PRIMARY KEY (id)
- UNIQUE (application_id)
- UNIQUE (receipt_number)
- INDEX (property_number)
- INDEX (payment_status)
- FOREIGN KEY (application_id) → application(id) ON DELETE CASCADE

**Tax Types:**
- water_tax (Water supply tax)
- house_tax (Property/House tax)

**Payment Methods:**
- online (UPI/Net Banking)
- cash (Cash payment)
- cheque (Cheque payment)
- dd (Demand Draft)

---

### 7. Complaint (portal_app_complaint)

**Purpose:** Complaint and grievance management

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInt | PRIMARY KEY | Auto-increment ID |
| complaint_number | VARCHAR(20) | UNIQUE, NOT NULL | Auto-generated (CMPxxxx...) |
| complainant_id | BigInt | FOREIGN KEY | → customuser.id |
| category | VARCHAR(20) | NOT NULL | Complaint category |
| subject | VARCHAR(300) | NOT NULL | Brief subject |
| description | TEXT | NOT NULL | Detailed description |
| location | TEXT | NOT NULL | Issue location |
| priority | VARCHAR(10) | DEFAULT 'medium' | low/medium/high/urgent |
| status | VARCHAR(15) | DEFAULT 'open' | open/in_progress/resolved/closed |
| complaint_photo | VARCHAR(100) | NULLABLE | Photo evidence |
| filed_date | DATETIME | AUTO | Submission timestamp |
| assigned_to_id | BigInt | FOREIGN KEY, NULLABLE | → customuser.id |
| resolved_date | DATETIME | NULLABLE | Resolution timestamp |
| resolution_remarks | TEXT | NULLABLE | Resolution details |

**Indexes:**
- PRIMARY KEY (id)
- UNIQUE (complaint_number)
- INDEX (complaint_number)
- INDEX (status)
- INDEX (complainant_id, status)
- FOREIGN KEY (complainant_id) → customuser(id) ON DELETE CASCADE
- FOREIGN KEY (assigned_to_id) → customuser(id) ON DELETE SET NULL

**Categories:**
- water_supply (Water supply issues)
- electricity (Power/Electricity)
- road (Road & Infrastructure)
- sanitation (Sanitation issues)
- street_light (Street lighting)
- drainage (Drainage problems)
- waste_management (Garbage/Waste)
- other (Other issues)

**Priority Levels:**
- low (Non-urgent)
- medium (Normal priority)
- high (Important)
- urgent (Critical/Emergency)

**Status Values:**
- open (Newly filed)
- in_progress (Being worked on)
- resolved (Issue resolved)
- closed (Completed)

---

### 8. ApplicationStatusHistory (portal_app_applicationstatushistory)

**Purpose:** Audit trail for application status changes

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BigInt | PRIMARY KEY | Auto-increment ID |
| application_id | BigInt | FOREIGN KEY | → application.id |
| old_status | VARCHAR(15) | NOT NULL | Previous status |
| new_status | VARCHAR(15) | NOT NULL | New status |
| changed_by_id | BigInt | FOREIGN KEY, NULLABLE | → customuser.id |
| changed_at | DATETIME | AUTO | Change timestamp |
| remarks | TEXT | NULLABLE | Change remarks |

**Indexes:**
- PRIMARY KEY (id)
- INDEX (changed_at)
- FOREIGN KEY (application_id) → application(id) ON DELETE CASCADE
- FOREIGN KEY (changed_by_id) → customuser(id) ON DELETE SET NULL

**Use Case:**
- Maintains complete history of all status changes
- Shows who changed status and when
- Useful for auditing and compliance
- Can track application progress over time

---

## Sample Data Queries

### Get All Pending Applications with Applicant Details
```sql
SELECT 
    a.application_number,
    a.application_type,
    a.applied_date,
    u.first_name,
    u.last_name,
    u.email,
    u.phone_number
FROM portal_app_application a
JOIN portal_app_customuser u ON a.applicant_id = u.id
WHERE a.status = 'pending'
ORDER BY a.applied_date DESC;
```

### Get Birth Certificate Details for Approved Applications
```sql
SELECT 
    a.application_number,
    bc.certificate_number,
    bc.child_name,
    bc.date_of_birth,
    bc.issued_date
FROM portal_app_birthcertificate bc
JOIN portal_app_application a ON bc.application_id = a.id
WHERE a.status = 'approved'
ORDER BY bc.issued_date DESC;
```

### Get Open Complaints by Category
```sql
SELECT 
    category,
    COUNT(*) as count
FROM portal_app_complaint
WHERE status = 'open'
GROUP BY category
ORDER BY count DESC;
```

### Get Application Status Change History
```sql
SELECT 
    a.application_number,
    ash.old_status,
    ash.new_status,
    ash.changed_at,
    u.first_name as changed_by
FROM portal_app_applicationstatushistory ash
JOIN portal_app_application a ON ash.application_id = a.id
LEFT JOIN portal_app_customuser u ON ash.changed_by_id = u.id
WHERE a.id = <application_id>
ORDER BY ash.changed_at;
```

---

## Database Size Estimates

**For 10,000 users over 1 year:**

| Table | Avg Rows | Avg Size per Row | Total Size |
|-------|----------|------------------|------------|
| CustomUser | 10,000 | 2 KB | 20 MB |
| Application | 50,000 | 1 KB | 50 MB |
| BirthCertificate | 10,000 | 2 KB | 20 MB |
| DeathCertificate | 5,000 | 2 KB | 10 MB |
| IncomeCertificate | 20,000 | 2 KB | 40 MB |
| TaxPayment | 15,000 | 1 KB | 15 MB |
| Complaint | 25,000 | 1 KB | 25 MB |
| ApplicationStatusHistory | 100,000 | 0.5 KB | 50 MB |
| **Total** | | | **~230 MB** |

**Note:** File uploads (PDFs, images) are stored separately in media folder

---

## Backup Strategy

### Daily Backup
```bash
mysqldump -u root -p gram_panchayat_db > backup_$(date +%Y%m%d).sql
```

### Weekly Full Backup
```bash
mysqldump -u root -p --all-databases > full_backup_$(date +%Y%m%d).sql
```

### Restore from Backup
```bash
mysql -u root -p gram_panchayat_db < backup_20260201.sql
```

---

**Database Version:** MySQL 8.0+  
**Character Set:** UTF8MB4  
**Collation:** utf8mb4_unicode_ci  
**Engine:** InnoDB (default)

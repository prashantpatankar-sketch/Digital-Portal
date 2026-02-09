# 🚀 QUICK START COMMANDS

## Initial Setup (One-time only)

### 1. Create Virtual Environment
```powershell
cd d:\portal
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
pip install argon2-cffi  # For secure password hashing
```

### 3. Create Database (MySQL)
```powershell
mysql -u root -p
```
```sql
CREATE DATABASE gram_panchayat_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES;
EXIT;
```

### 4. Configure Environment
```powershell
# Create .env file with:
DB_ENGINE=mysql
DB_NAME=gram_panchayat_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### 5. Run Migrations
```powershell
python manage.py makemigrations
python manage.py migrate
```

Expected migrations:
- portal_app.0001_initial (all models)
- portal_app.0002_alter_customuser_role (role-based auth)

### 6. Create Admin User
```powershell
python manage.py createsuperuser
# Username: admin
# Email: admin@grampanchayat.gov.in
# Password: (min 8 characters)
```

---

## Database Commands

### View Database Structure
```powershell
# Django shell
python manage.py dbshell
```

```sql
-- Show all tables
SHOW TABLES;

-- Describe specific table
DESCRIBE portal_app_customuser;
DESCRIBE portal_app_application;
DESCRIBE portal_app_birthcertificate;
DESCRIBE portal_app_taxpayment;
DESCRIBE portal_app_complaint;

-- Show indexes
SHOW INDEX FROM portal_app_application;

-- Count records
SELECT COUNT(*) FROM portal_app_customuser;
SELECT COUNT(*) FROM portal_app_application;

-- View users by role
SELECT role, COUNT(*) FROM portal_app_customuser GROUP BY role;

-- View applications by status
SELECT status, COUNT(*) FROM portal_app_application GROUP BY status;

EXIT;
```

### Create Sample Data
```powershell
python manage.py shell
```

```python
from portal_app.models import CustomUser, Application, BirthCertificate
from datetime import date

# Create citizen
citizen = CustomUser.objects.create_user(
    username='ramesh',
    password='Test@1234',
    first_name='Ramesh',
    last_name='Kumar',
    email='ramesh@example.com',
    phone_number='9876543210',
    role='citizen',
    address='123 Main Street',
    village='Model Village',
    pincode='123456'
)

# Create application
app = Application.objects.create(
    applicant=citizen,
    application_type='birth_certificate',
    status='pending'
)

print(f"Application created: {app.application_number}")
exit()
```

### Check Database Status
```powershell
# Show migration status
python manage.py showmigrations

# Check for missing migrations
python manage.py makemigrations --dry-run

# Verify database connection
python manage.py check --database default
```

---

## Daily Development Commands

### Start Server
```powershell
cd d:\portal\gram_panchayat
venv\Scripts\activate
python manage.py runserver
```

**Access:**
- Homepage: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

### Stop Server
```
Ctrl + C
```

---

## Common Management Commands

### Database Operations

**Make new migrations (after model changes):**
```powershell
python manage.py makemigrations
```

**Apply migrations:**
```powershell
python manage.py migrate
```

**Show migrations status:**
```powershell
python manage.py showmigrations
```

**Reset database (DANGER - deletes all data):**
```powershell
python manage.py flush
```

---

### User Management

**Create superuser:**
```powershell
python manage.py createsuperuser
```

**Change user password:**
```powershell
python manage.py changepassword <username>
```

---

### Static Files

**Collect static files (for production):**
```powershell
python manage.py collectstatic
```

---

### Shell & Debug

**Open Django shell:**
```powershell
python manage.py shell
```

**Example shell commands:**
```python
from portal_app.models import CustomUser, Application

# Get all users
users = CustomUser.objects.all()

# Get pending applications
pending = Application.objects.filter(status='pending')

# Count applications
Application.objects.count()

# Exit shell
exit()
```

**Check for errors:**
```powershell
python manage.py check
```

---

### Database Backup & Restore

**Backup database:**
```powershell
mysqldump -u root -p gram_panchayat_db > backup.sql
```

**Restore database:**
```powershell
mysql -u root -p gram_panchayat_db < backup.sql
```

---

## Testing URLs

### Public Pages
- Homepage: http://127.0.0.1:8000/
- About: http://127.0.0.1:8000/about/
- Services: http://127.0.0.1:8000/services/
- Track Application: http://127.0.0.1:8000/track/
- Login: http://127.0.0.1:8000/login/
- Register: http://127.0.0.1:8000/register/

### Citizen Pages (Requires Login)
- Dashboard: http://127.0.0.1:8000/dashboard/
- Birth Certificate: http://127.0.0.1:8000/apply/birth-certificate/
- Death Certificate: http://127.0.0.1:8000/apply/death-certificate/
- Income Certificate: http://127.0.0.1:8000/apply/income-certificate/
- Pay Tax: http://127.0.0.1:8000/pay-tax/
- File Complaint: http://127.0.0.1:8000/file-complaint/
- My Applications: http://127.0.0.1:8000/my-applications/
- My Complaints: http://127.0.0.1:8000/my-complaints/

### Admin Pages (Requires Admin Login)
- Django Admin: http://127.0.0.1:8000/admin/
- Admin Dashboard: http://127.0.0.1:8000/admin-dashboard/
- Manage Applications: http://127.0.0.1:8000/admin/applications/
- Manage Complaints: http://127.0.0.1:8000/admin/complaints/

---

## Troubleshooting Commands

### Module not found error:
```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

### Port already in use:
```powershell
# Run on different port
python manage.py runserver 8080
```

### MySQL connection error:
```powershell
# Test MySQL connection
mysql -u root -p
```

### Clear migrations (NUCLEAR OPTION):
```powershell
# Delete migration files (keep __init__.py)
# Then:
python manage.py makemigrations
python manage.py migrate
```

### View Django logs:
```powershell
# Django shows logs in terminal where runserver is running
# Check terminal output
```

---

## Quick Data Creation (for Testing)

### Using Django Shell
```powershell
python manage.py shell
```

```python
from portal_app.models import CustomUser
from django.contrib.auth.hashers import make_password

# Create test citizen
citizen = CustomUser.objects.create(
    username='testcitizen',
    password=make_password('Test@1234'),
    email='citizen@test.com',
    first_name='Test',
    last_name='Citizen',
    role='citizen',
    phone_number='9876543210',
    address='Test Address',
    village='Test Village',
    pincode='400001'
)

print(f"Created user: {citizen.username}")
```

---

## Environment Variables Reference

### .env file contents:
```
# Database
DB_ENGINE=mysql
DB_NAME=gram_panchayat_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## File Structure Reference

```
portal/
├── gram_panchayat/           # cd here to run commands
│   ├── manage.py             # Django management script
│   ├── settings.py           # Configuration
│   └── urls.py               # URL routing
├── portal_app/               # Main app
│   ├── models.py             # Database models
│   ├── views.py              # Business logic
│   ├── forms.py              # Form definitions
│   └── templates/            # HTML files
├── static/                   # CSS, JS, Images
├── media/                    # User uploads
├── requirements.txt          # Dependencies
└── .env                      # Environment vars
```

---

## Git Commands (Version Control)

### Initialize Git (One-time):
```powershell
git init
git add .
git commit -m "Initial commit"
```

### Regular commits:
```powershell
git status
git add .
git commit -m "Your commit message"
```

### Create .gitignore (already created):
```
__pycache__/
*.pyc
.env
media/
staticfiles/
venv/
```

---

## 🧪 Testing Commands

### Create Test Data
```powershell
# Create test users and sample data
python manage.py create_test_data

# This creates:
# - Admin user (admin / Admin@123)
# - Staff user (staff1 / Staff@123)
# - 3 Citizen users (citizen1, citizen2, citizen3 / Citizen@123)
# - Sample applications (birth, death, income certificates)
# - Sample complaints
# - Sample tax payments
```

### Test User Credentials
```
Admin:
  Username: admin
  Password: Admin@123
  Access: Full system

Staff:
  Username: staff1
  Password: Staff@123
  Access: Application processing

Citizens:
  Username: citizen1, citizen2, citizen3
  Password: Citizen@123 (all)
  Access: Submit applications, complaints
```

### Manual Testing Checklist
```powershell
# 1. Test Registration
# Go to: http://127.0.0.1:8000/register/
# Try: Valid data, duplicate email, weak password

# 2. Test Login
# Go to: http://127.0.0.1:8000/login/
# Try: Correct credentials, wrong password, each role

# 3. Test Applications
# Login as citizen1
# Submit: Birth certificate, Death certificate, Income certificate
# Verify: Application number generated, status tracking

# 4. Test Staff Processing
# Login as staff1
# Go to pending applications
# Try: Approve, Reject, Under Review

# 5. Test Admin Dashboard
# Login as admin
# View: Statistics, charts, user management

# 6. Test Security
# Try: Access staff area as citizen (should block)
# Try: Access admin area as staff (should block)
# Try: File upload >5MB (should reject)
```

### Run Automated Tests
```powershell
# Run all tests
python manage.py test

# Run specific test module
python manage.py test portal_app.tests

# Run with coverage
pip install coverage
coverage run manage.py test
coverage report
coverage html  # Generate HTML report
```

### View Testing Guide
```powershell
# Open comprehensive testing documentation
code TESTING_GUIDE.md

# Contents:
# - Test user accounts
# - Test cases for all features
# - Real-world scenarios
# - Error handling tests
# - Security testing
# - Performance testing
```

### Quick Test Scenarios

#### Scenario 1: New Citizen Journey
```powershell
# 1. Register new account
# 2. Login
# 3. Submit birth certificate application
# 4. Track application status
# 5. View in dashboard
```

#### Scenario 2: Staff Processing
```powershell
# 1. Login as staff
# 2. View pending applications
# 3. Review application details
# 4. Approve/Reject with remarks
# 5. Verify status update
```

#### Scenario 3: File Complaint
```powershell
# 1. Login as citizen
# 2. File complaint (Road/Water/Lights)
# 3. Track complaint status
# 4. View resolution (if resolved)
```

### Error Testing
```powershell
# Test invalid inputs
# - Invalid email format
# - Phone number with wrong prefix
# - Aadhar less than 12 digits
# - Weak password
# - Large file upload (>5MB)
# - Wrong file type (.exe, .zip)

# Test security
# - XSS attempt in username: <script>alert('XSS')</script>
# - SQL injection attempt: admin' OR '1'='1
# - Access unauthorized URLs
# - CSRF token removal
```

### Performance Testing
```powershell
# Install Apache Bench (optional)
# Test home page load
ab -n 100 -c 10 http://127.0.0.1:8000/

# Test with multiple concurrent users
# - 10 users browsing
# - 5 users submitting forms
# - Monitor response times
```

---

## � OTP Email Verification Commands

### Test OTP in Development
```powershell
# Start server (OTP will print in console)
python manage.py runserver

# Register new user at: http://127.0.0.1:8000/register/
# Check console/terminal for OTP code
# Example output:
# ----------------------------------------------------------------------
# Subject: Email Verification OTP
# Your Verification Code: 123456
# ----------------------------------------------------------------------

# Copy OTP and verify at: http://127.0.0.1:8000/verify-otp/
```

### Configure Production Email (Gmail)
```powershell
# 1. Enable 2FA on Google Account
# 2. Generate App Password: https://myaccount.google.com/apppasswords
# 3. Add to .env file:

# .env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop  # 16-char app password
DEFAULT_FROM_EMAIL=noreply@grampanchayat.gov.in
```

### Test Email Sending
```powershell
# Django shell test
python manage.py shell

# In shell:
from django.core.mail import send_mail
send_mail(
    'Test Email',
    'This is a test message',
    'noreply@grampanchayat.gov.in',
    ['test@example.com'],
    fail_silently=False,
)
# Check if email received
```

### OTP Management Commands
```powershell
# View all OTPs (Django admin)
# Login to: http://127.0.0.1:8000/admin/
# Navigate to: Email OTPs

# Delete expired OTPs (Django shell)
python manage.py shell
from portal_app.models import EmailOTP
from django.utils import timezone
EmailOTP.objects.filter(expires_at__lt=timezone.now()).delete()

# Check OTP success rate
python manage.py shell
from portal_app.models import EmailOTP
from django.utils import timezone
from datetime import timedelta

recent = EmailOTP.objects.filter(
    created_at__gte=timezone.now() - timedelta(days=1)
)
total = recent.count()
verified = recent.filter(is_verified=True).count()
print(f"Success Rate: {verified/total*100:.2f}%")
```

### Troubleshooting OTP Issues
```powershell
# Issue: OTP not received
# Development: Check console output
# Production: Check email spam folder, verify SMTP settings

# Issue: OTP expired immediately
# Check server time: Get-Date (PowerShell)
# Verify timezone in settings.py: TIME_ZONE = 'Asia/Kolkata'

# Issue: Maximum attempts exceeded
# Delete old OTPs:
python manage.py shell
from portal_app.models import EmailOTP
EmailOTP.objects.filter(user__username='testuser', is_used=False).delete()

# Issue: User can login without verification
# Check is_active and email_verified fields:
python manage.py shell
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='testuser')
print(f"Active: {user.is_active}, Verified: {user.email_verified}")
```

### OTP Documentation
```powershell
# View comprehensive OTP guide
code OTP_VERIFICATION_GUIDE.md

# Contents:
# - Complete OTP flow diagram
# - Security features explained
# - Model changes details
# - Email configuration guide
# - Testing procedures
# - Troubleshooting guide
# - Production deployment checklist
```

---

## �🔐 Security Commands

### Check Security Configuration
```powershell
# Run Django security check
python manage.py check --deploy

# Basic system check
python manage.py check
```

### Install Security Dependencies
```powershell
# Install Argon2 password hasher (most secure)
pip install argon2-cffi

# Check for package vulnerabilities
pip install safety
safety check

# Keep packages updated
pip list --outdated
```

### Test Password Validators
```powershell
python manage.py shell
```
```python
from django.contrib.auth.password_validation import validate_password

# Test password strength
try:
    validate_password("weak")
except Exception as e:
    print(e)  # Will show validation errors

# Test strong password
validate_password("StrongP@ss123!")  # Should pass
```

### Security Testing in Shell
```powershell
python manage.py shell
```
```python
# Test password hashing
from portal_app.models import CustomUser
user = CustomUser.objects.create_user(
    username='testuser',
    password='TestPass123!'
)
print(user.password)  # Will show Argon2 hash

# Test file validation
from portal_app.security_utils import validate_file_upload
# (test with actual file object)

# Test rate limiting
from portal_app.security_utils import check_rate_limit
result = check_rate_limit('test_user', limit=5, period=60)
print(f"Rate limit OK: {result}")

# Check password strength
from portal_app.security_utils import check_password_strength
strength = check_password_strength("MyPass123!")
print(strength)
```

### Security Documentation
```powershell
# View comprehensive security guide
code SECURITY_IMPLEMENTATION_GUIDE.md

# View quick reference
code SECURITY_QUICK_REFERENCE.md
```

### Generate Strong Secret Key
```powershell
python manage.py shell
```
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
# Copy this to your .env file as SECRET_KEY
```

### Security Checklist Before Production
```powershell
# 1. Check all security settings
python manage.py check --deploy

# 2. Verify .env configuration
# DEBUG=False
# SECRET_KEY=<strong-random-key>
# ALLOWED_HOSTS=yourdomain.com

# 3. Test authentication
# - Try login with wrong password (should block after 5 attempts)
# - Test role-based access
# - Verify session timeout

# 4. Test file uploads
# - Upload large file (should reject >5MB)
# - Upload wrong file type (should reject)

# 5. Check HTTPS configuration (production only)
# - All cookies should have Secure flag
# - HSTS headers enabled
```

---

## Production Deployment Checklist

Before deploying to production:

- [ ] Set `DEBUG=False` in .env
- [ ] Generate strong `SECRET_KEY` and add to .env
- [ ] Update `ALLOWED_HOSTS` with your domain
- [ ] Install `argon2-cffi` for password hashing
- [ ] Set up HTTPS/SSL certificate
- [ ] Enable all security headers (already in settings.py)
- [ ] Configure static files collection
- [ ] Set up database backups
- [ ] Configure email settings (for notifications)
- [ ] Set up security logging
- [ ] Run `python manage.py check --deploy`
- [ ] Test all security features
- [ ] Create admin documentation
- [ ] Review all user roles and permissions

### Security Features Checklist
- [x] CSRF protection enabled
- [x] Password hashing (Argon2)
- [x] Form validation (all inputs)
- [x] Role-based access control
- [x] SQL injection prevention (Django ORM)
- [x] XSS prevention (template escaping)
- [x] File upload security
- [x] Session security (1-hour timeout)
- [x] Security headers (production)
- [x] Rate limiting utilities
- [x] Security logging utilities

---

## Support & Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **Bootstrap 5 Docs**: https://getbootstrap.com/docs/5.3/
- **MySQL Documentation**: https://dev.mysql.com/doc/
- **Python Documentation**: https://docs.python.org/3/

---

## Quick Reference: Default Test Credentials

**Admin (Create using createsuperuser):**
- Username: admin
- Password: (your choice)
- URL: http://127.0.0.1:8000/admin/

**Test Citizen (Create via registration):**
- URL: http://127.0.0.1:8000/register/
- Create your own account

---

**Save this file as:** `QUICK_COMMANDS.md`  
**Keep it handy for daily development!**

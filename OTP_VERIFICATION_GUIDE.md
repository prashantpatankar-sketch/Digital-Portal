# OTP-Based Email Verification System
## Digital Gram Panchayat Portal

Complete implementation guide for secure OTP-based email verification system.

---

## Table of Contents

1. [Overview](#overview)
2. [OTP Flow Diagram](#otp-flow-diagram)
3. [Security Features](#security-features)
4. [Architecture](#architecture)
5. [Model Changes](#model-changes)
6. [Implementation Details](#implementation-details)
7. [Email Configuration](#email-configuration)
8. [Testing Guide](#testing-guide)
9. [Troubleshooting](#troubleshooting)
10. [Production Deployment](#production-deployment)

---

## Overview

### What is OTP Email Verification?

OTP (One-Time Password) email verification is a security mechanism that ensures users provide a valid email address during registration. The system sends a 6-digit code to the user's email, which must be verified before account activation.

### Key Features

✅ **6-digit OTP** sent to user's email  
✅ **10-minute expiration** for enhanced security  
✅ **Maximum 3 verification attempts** per OTP  
✅ **One-time use** - OTP cannot be reused  
✅ **Rate limiting** - 1 OTP request per minute  
✅ **Secure generation** using Python's `secrets` module  
✅ **Account inactive** until email verified  
✅ **Beautiful email templates** with responsive design  
✅ **Real-time countdown timer** on verification page  

---

## OTP Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    OTP VERIFICATION FLOW                          │
└─────────────────────────────────────────────────────────────────┘

1. USER REGISTRATION
   ┌─────────────┐
   │   User      │
   │  Fills      │──────▶ Registration Form
   │   Form      │        (Name, Email, Password, etc.)
   └─────────────┘
          │
          ▼
   ┌─────────────────────────────────────┐
   │  Account Created                     │
   │  - is_active = False                │
   │  - email_verified = False            │
   └─────────────────────────────────────┘
          │
          ▼

2. OTP GENERATION
   ┌─────────────────────────────────────┐
   │  generate_otp()                      │
   │  - Uses secrets module               │
   │  - Generates 6-digit code            │
   │  - Creates EmailOTP record           │
   │  - Sets 10-minute expiration         │
   └─────────────────────────────────────┘
          │
          ▼

3. EMAIL SENDING
   ┌─────────────────────────────────────┐
   │  send_otp_email()                    │
   │  - Loads email template              │
   │  - Sends HTML email                  │
   │  - Includes OTP code                 │
   │  - Shows expiry time                 │
   └─────────────────────────────────────┘
          │
          ▼

4. USER RECEIVES EMAIL
   ┌─────────────────────────────────────┐
   │  Email Contains:                     │
   │  ✉️  6-digit OTP code               │
   │  ⏰  10-minute expiration           │
   │  🔒  Security warnings              │
   │  📋  Verification instructions      │
   └─────────────────────────────────────┘
          │
          ▼

5. OTP VERIFICATION PAGE
   ┌─────────────────────────────────────┐
   │  User Enters OTP                     │
   │  - Input: 6-digit code               │
   │  - Shows: Attempts remaining         │
   │  - Shows: Time countdown             │
   │  - Button: Resend OTP                │
   └─────────────────────────────────────┘
          │
          ▼

6. OTP VALIDATION
   ┌─────────────────────────────────────┐
   │  verify_otp()                        │
   │  ✓ Check if OTP exists               │
   │  ✓ Check if not expired              │
   │  ✓ Check attempts < 3                │
   │  ✓ Check if not used                 │
   │  ✓ Validate OTP code                 │
   └─────────────────────────────────────┘
          │
          ├──────▶ INVALID
          │       ├─ Increment attempts
          │       ├─ Show error message
          │       └─ Attempts remaining: X/3
          │
          └──────▶ VALID
                  │
                  ▼
          ┌─────────────────────────────────────┐
          │  Account Activation                  │
          │  - email_verified = True             │
          │  - is_active = True                  │
          │  - email_verified_at = now()         │
          │  - OTP marked as used                │
          └─────────────────────────────────────┘
                  │
                  ▼
          ┌─────────────────────────────────────┐
          │  Redirect to Login                   │
          │  ✅ Account activated!              │
          │  ✅ User can now login              │
          └─────────────────────────────────────┘

RESEND OTP FLOW (if OTP expires or not received):
   ┌─────────────────────────────────────┐
   │  User clicks "Resend OTP"            │
   └─────────────────────────────────────┘
          │
          ▼
   ┌─────────────────────────────────────┐
   │  Rate Limit Check                    │
   │  - Last OTP < 1 minute ago? BLOCK    │
   │  - Otherwise: ALLOW                  │
   └─────────────────────────────────────┘
          │
          ▼
   ┌─────────────────────────────────────┐
   │  Invalidate Previous OTPs            │
   │  - Mark all old OTPs as used         │
   └─────────────────────────────────────┘
          │
          ▼
   ┌─────────────────────────────────────┐
   │  Generate & Send New OTP             │
   │  - New 6-digit code                  │
   │  - New 10-minute timer               │
   │  - Fresh 3 attempts                  │
   └─────────────────────────────────────┘
```

---

## Security Features

### 1. Secure OTP Generation

**Implementation:**
```python
def generate_otp():
    import secrets
    return str(secrets.randbelow(900000) + 100000)
```

**Security:**
- Uses `secrets` module (cryptographically secure)
- Generates random 6-digit code (100000-999999)
- Avoids predictable patterns
- No sequential or timestamp-based codes

### 2. OTP Expiration (10 Minutes)

**Database Field:**
```python
expires_at = models.DateTimeField(
    help_text="When OTP expires (10 minutes from creation)"
)
```

**Automatic Expiration:**
```python
def save(self, *args, **kwargs):
    if not self.pk and not self.expires_at:
        from django.utils import timezone
        from datetime import timedelta
        self.expires_at = timezone.now() + timedelta(minutes=10)
    super().save(*args, **kwargs)
```

**Why 10 minutes?**
- Long enough for user to receive and enter OTP
- Short enough to prevent unauthorized access
- Industry standard for OTP systems
- Reduces window for brute-force attacks

### 3. Maximum 3 Verification Attempts

**Attempt Tracking:**
```python
verification_attempts = models.IntegerField(
    default=0,
    help_text="Number of verification attempts (max 3)"
)
```

**Validation Logic:**
```python
if otp.verification_attempts >= 3:
    otp.is_used = True
    otp.save()
    return False, "Maximum attempts exceeded. Please request a new OTP."
```

**Why 3 attempts?**
- Prevents brute-force attacks
- Reasonable for user mistakes (typos)
- Forces new OTP generation after 3 failures
- Logs all failed attempts for security auditing

### 4. One-Time Use Only

**Database Fields:**
```python
is_used = models.BooleanField(
    default=False,
    help_text="Whether this OTP has been used (one-time use)"
)

is_verified = models.BooleanField(
    default=False,
    help_text="Whether this OTP has been successfully verified"
)
```

**Enforcement:**
```python
def mark_as_verified(self):
    from django.utils import timezone
    self.is_verified = True
    self.is_used = True  # Can't be used again
    self.verified_at = timezone.now()
    self.save()
```

### 5. Rate Limiting (1 OTP per Minute)

**Implementation:**
```python
def resend_otp(user):
    from datetime import timedelta
    
    recent_otp = EmailOTP.objects.filter(
        user=user,
        created_at__gte=timezone.now() - timedelta(minutes=1)
    ).first()
    
    if recent_otp:
        return False, "Please wait 1 minute before requesting a new OTP."
```

**Prevents:**
- Email bombing
- Spam attacks
- Server resource exhaustion
- Abuse of email sending service

### 6. Account Inactive Until Verified

**User Model Fields:**
```python
email_verified = models.BooleanField(default=False)
is_active = models.BooleanField(default=False)
```

**Login Check:**
```python
if not user.email_verified:
    messages.warning(request, 'Your email is not verified.')
    return redirect('verify_otp')
```

**Why this is secure:**
- Prevents fake email registrations
- Ensures valid contact information
- Blocks automated bot registrations
- Confirms user owns the email address

### 7. Security Logging

**All OTP events are logged:**
- OTP generation
- OTP verification attempts (success/failure)
- Maximum attempts exceeded
- OTP expiration
- Rate limiting violations
- Email sending failures

**Example Log Entry:**
```python
log_security_event(
    'OTP_VERIFICATION_FAILED',
    user.username,
    f"Invalid OTP code entered (Attempt {otp.verification_attempts}/3)",
    'WARNING'
)
```

---

## Architecture

### Models Layer

#### EmailOTP Model
```python
class EmailOTP(models.Model):
    user = ForeignKey(CustomUser)        # User receiving OTP
    email = EmailField()                  # Email address
    otp_code = CharField(max_length=6)   # 6-digit code
    is_verified = BooleanField()         # Verification status
    is_used = BooleanField()             # One-time use flag
    verification_attempts = IntegerField() # Attempt counter
    created_at = DateTimeField()         # Creation timestamp
    expires_at = DateTimeField()         # Expiration timestamp
    verified_at = DateTimeField()        # Verification timestamp
```

#### CustomUser Model (Updated)
```python
class CustomUser(AbstractUser):
    # ... existing fields ...
    
    email_verified = BooleanField(default=False)
    email_verified_at = DateTimeField(null=True, blank=True)
    is_active = BooleanField(default=False)  # Requires email verification
```

### Security Utils Layer

**Key Functions:**
- `generate_otp()` - Secure OTP generation
- `create_otp_for_user(user)` - Create OTP record
- `verify_otp(user, otp_code)` - Validate OTP
- `send_otp_email(user, otp_code)` - Send email
- `resend_otp(user)` - Resend with rate limiting

### Views Layer

**Authentication Flow:**
1. `register_view()` - Create account, generate OTP, send email
2. `verify_otp_view()` - Display verification page, validate OTP
3. `resend_otp_view()` - Resend OTP with rate limiting
4. `login_view()` - Check email verification before login

### Forms Layer

**OTPVerificationForm:**
- 6-digit numeric input
- Client-side validation (pattern, maxlength)
- Server-side validation (digits only)
- Auto-formatting and styling

---

## Model Changes

### Database Schema Changes

#### New Table: `EmailOTP`

```sql
CREATE TABLE portal_app_emailotp (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    email           VARCHAR(254) NOT NULL,
    otp_code        VARCHAR(6) NOT NULL,
    is_verified     BOOLEAN NOT NULL DEFAULT 0,
    is_used         BOOLEAN NOT NULL DEFAULT 0,
    verification_attempts INTEGER NOT NULL DEFAULT 0,
    created_at      DATETIME NOT NULL,
    expires_at      DATETIME NOT NULL,
    verified_at     DATETIME NULL,
    
    FOREIGN KEY (user_id) REFERENCES portal_app_customuser(id)
);

CREATE INDEX idx_user_verified ON portal_app_emailotp(user_id, is_verified);
CREATE INDEX idx_email_otp ON portal_app_emailotp(email, otp_code);
```

#### Updated Table: `CustomUser`

```sql
ALTER TABLE portal_app_customuser 
ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 0;

ALTER TABLE portal_app_customuser 
ADD COLUMN email_verified_at DATETIME NULL;

-- Note: is_active now defaults to FALSE
```

### Migration File

The migration will be created with:
```bash
python manage.py makemigrations
python manage.py migrate
```

**Expected Migration:**
- Adds `email_verified` field to CustomUser
- Adds `email_verified_at` field to CustomUser
- Creates `EmailOTP` model
- Creates indexes for performance

---

## Implementation Details

### 1. Registration Flow (Updated)

**File: `portal_app/views.py`**

```python
def register_view(request):
    if request.method == 'POST':
        form = CitizenRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False          # ← INACTIVE until verified
            user.email_verified = False     # ← NOT verified
            user.save()
            
            # Generate and send OTP
            from .security_utils import create_otp_for_user, send_otp_email
            
            otp = create_otp_for_user(user)
            
            if send_otp_email(user, otp.otp_code):
                messages.success(request, f'OTP sent to {user.email}')
                request.session['pending_verification_user_id'] = user.id
                return redirect('verify_otp')
```

**Key Points:**
- Account created as inactive
- OTP generated immediately
- Email sent with OTP code
- User ID stored in session
- Redirects to OTP verification page

### 2. OTP Verification View

**File: `portal_app/views.py`**

```python
def verify_otp_view(request):
    # Get user from session
    user_id = request.session.get('pending_verification_user_id')
    user = CustomUser.objects.get(id=user_id)
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data.get('otp_code')
            
            # Verify OTP
            success, message = verify_otp(user, otp_code)
            
            if success:
                # OTP verified successfully
                # User activated automatically in verify_otp()
                return redirect('login')
```

**Security Checks:**
1. Validates session
2. Checks if already verified
3. Validates OTP format (6 digits)
4. Calls `verify_otp()` function
5. Handles all error cases

### 3. Login Flow (Updated)

**File: `portal_app/views.py`**

```python
def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(...)
            
            # NEW: Check email verification
            if not user.email_verified:
                messages.warning(request, 'Email not verified')
                # Resend OTP
                otp = create_otp_for_user(user)
                send_otp_email(user, otp.otp_code)
                return redirect('verify_otp')
            
            # Proceed with login...
```

**Why check at login?**
- Catches users who closed browser after registration
- Automatically resends OTP if needed
- Prevents login without verification
- User-friendly experience

### 4. OTP Generation (Secure)

**File: `portal_app/security_utils.py`**

```python
def generate_otp():
    import secrets
    return str(secrets.randbelow(900000) + 100000)
```

**Why `secrets` module?**
- Cryptographically secure random number generator
- Better than `random` module for security
- Recommended by Python documentation
- Used in production systems worldwide

**Formula Breakdown:**
```python
secrets.randbelow(900000)  # Returns 0 to 899999
+ 100000                    # Adds 100000
= 100000 to 999999         # 6-digit range
```

### 5. Email Sending

**File: `portal_app/security_utils.py`**

```python
def send_otp_email(user, otp_code):
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    
    html_message = render_to_string('portal_app/emails/otp_verification.html', {
        'user': user,
        'otp_code': otp_code,
        'expiry_minutes': 10,
    })
    
    send_mail(
        subject='Email Verification OTP',
        message=strip_tags(html_message),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
```

**Email Template Features:**
- Beautiful HTML design
- Responsive layout
- Clear OTP display (large font)
- Security warnings
- Expiry information
- Instructions for verification

### 6. OTP Validation Logic

**File: `portal_app/security_utils.py`**

```python
def verify_otp(user, otp_code):
    # Get latest OTP
    otp = EmailOTP.objects.filter(
        user=user,
        is_used=False
    ).order_by('-created_at').first()
    
    # Check 1: OTP exists
    if not otp:
        return False, "No valid OTP found"
    
    # Check 2: Not expired
    if timezone.now() > otp.expires_at:
        return False, "OTP has expired"
    
    # Check 3: Attempts < 3
    if otp.verification_attempts >= 3:
        otp.is_used = True
        otp.save()
        return False, "Maximum attempts exceeded"
    
    # Increment attempts
    otp.increment_attempts()
    
    # Check 4: Validate code
    if otp.otp_code == otp_code:
        # SUCCESS
        otp.mark_as_verified()
        
        # Activate user
        user.email_verified = True
        user.email_verified_at = timezone.now()
        user.is_active = True
        user.save()
        
        return True, "Email verified successfully!"
    else:
        # FAILURE
        attempts_left = 3 - otp.verification_attempts
        return False, f"Invalid OTP. {attempts_left} attempts remaining"
```

**Validation Order:**
1. OTP exists
2. Not expired
3. Attempts < 3
4. Code matches

**Why this order?**
- Fails fast on obvious issues
- Prevents unnecessary processing
- Gives clear error messages
- Increments attempts only after basic checks

---

## Email Configuration

### Development Environment

**File: `gram_panchayat/settings.py`**

```python
# Development: Print emails to console
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**Testing OTP:**
1. Register a new user
2. Check terminal/console output
3. Copy OTP code from console
4. Enter on verification page

**Example Console Output:**
```
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: Email Verification OTP - Digital Gram Panchayat Portal
From: noreply@grampanchayat.gov.in
To: user@example.com
Date: Thu, 06 Feb 2026 10:30:00 -0000

Your Verification Code: 123456
This code expires in 10 minutes.
```

### Production Environment (Gmail SMTP)

**1. Create Environment Variables (.env file):**

```env
DEBUG=False
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@grampanchayat.gov.in
```

**2. Gmail App Password Setup:**

a) Go to Google Account settings
b) Enable 2-Factor Authentication
c) Generate App Password:
   - Go to: https://myaccount.google.com/apppasswords
   - Select App: "Mail"
   - Select Device: "Other (Custom name)"
   - Name it: "Django Portal"
   - Copy generated 16-character password

**3. Update .env file:**
```env
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop  # 16-character app password
```

**4. Settings Configuration:**

```python
# Production: SMTP backend
if not DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@grampanchayat.gov.in')
```

### Production Environment (Custom SMTP)

**For custom email servers (cPanel, AWS SES, SendGrid, etc.):**

```env
EMAIL_HOST=smtp.yourdomain.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

**Common SMTP Providers:**

| Provider | Host | Port | TLS |
|----------|------|------|-----|
| Gmail | smtp.gmail.com | 587 | Yes |
| Outlook | smtp.office365.com | 587 | Yes |
| SendGrid | smtp.sendgrid.net | 587 | Yes |
| AWS SES | email-smtp.region.amazonaws.com | 587 | Yes |
| Mailgun | smtp.mailgun.org | 587 | Yes |

---

## Testing Guide

### Manual Testing Steps

**1. Test User Registration with OTP:**

```bash
# Start development server
python manage.py runserver

# Open browser: http://127.0.0.1:8000/register/
```

1. Fill registration form:
   - Username: testuser1
   - Email: test@example.com
   - Password: Test@123
   - Other required fields

2. Submit form

3. Check console output for OTP:
   ```
   Your Verification Code: 234567
   ```

4. Copy OTP code

5. Go to verification page (automatic redirect)

6. Enter OTP

7. Click "Verify Email"

8. Should see success message

9. Try logging in

**2. Test OTP Expiration:**

1. Register new user
2. Get OTP from console
3. Wait 10 minutes
4. Try to verify
5. Should see "OTP has expired" error
6. Click "Resend OTP"
7. Get new OTP
8. Verify successfully

**3. Test Maximum Attempts:**

1. Register new user
2. Get OTP from console
3. Enter wrong OTP (first attempt)
4. Enter wrong OTP (second attempt)
5. Enter wrong OTP (third attempt)
6. Should see "Maximum attempts exceeded"
7. Click "Resend OTP"
8. Get new OTP with fresh 3 attempts

**4. Test Rate Limiting:**

1. Register new user
2. Click "Resend OTP" immediately
3. Click "Resend OTP" again within 1 minute
4. Should see rate limit error
5. Wait 1 minute
6. Click "Resend OTP" again
7. Should work successfully

**5. Test Login Without Verification:**

1. Register new user
2. Close browser (don't verify)
3. Go to login page directly
4. Try to login with credentials
5. Should show "Email not verified"
6. Should receive new OTP
7. Should redirect to verification page

### Automated Testing

**Create test file: `portal_app/tests/test_otp.py`**

```python
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from portal_app.models import EmailOTP
from portal_app.security_utils import generate_otp, create_otp_for_user, verify_otp
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class OTPTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Test@123',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '9876543210',
            'address': 'Test Address',
            'village': 'Test Village',
            'pincode': '123456'
        }
    
    def test_otp_generation(self):
        """Test OTP is 6 digits"""
        otp = generate_otp()
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())
    
    def test_otp_creation(self):
        """Test OTP record creation"""
        user = User.objects.create_user(**self.user_data)
        otp_record = create_otp_for_user(user)
        
        self.assertEqual(otp_record.user, user)
        self.assertEqual(otp_record.email, user.email)
        self.assertEqual(len(otp_record.otp_code), 6)
        self.assertFalse(otp_record.is_verified)
        self.assertFalse(otp_record.is_used)
    
    def test_otp_expiration(self):
        """Test OTP expires after 10 minutes"""
        user = User.objects.create_user(**self.user_data)
        otp_record = create_otp_for_user(user)
        
        # Should be valid initially
        self.assertTrue(otp_record.is_valid())
        
        # Simulate 10 minutes passing
        otp_record.expires_at = timezone.now() - timedelta(seconds=1)
        otp_record.save()
        
        # Should be expired now
        self.assertFalse(otp_record.is_valid())
    
    def test_otp_verification_success(self):
        """Test successful OTP verification"""
        user = User.objects.create_user(**self.user_data)
        user.is_active = False
        user.email_verified = False
        user.save()
        
        otp_record = create_otp_for_user(user)
        
        # Verify OTP
        success, message = verify_otp(user, otp_record.otp_code)
        
        self.assertTrue(success)
        self.assertIn('success', message.lower())
        
        # Check user activation
        user.refresh_from_db()
        self.assertTrue(user.email_verified)
        self.assertTrue(user.is_active)
    
    def test_otp_verification_failure(self):
        """Test OTP verification with wrong code"""
        user = User.objects.create_user(**self.user_data)
        otp_record = create_otp_for_user(user)
        
        # Try wrong OTP
        success, message = verify_otp(user, '000000')
        
        self.assertFalse(success)
        self.assertIn('Invalid', message)
    
    def test_otp_max_attempts(self):
        """Test maximum 3 attempts"""
        user = User.objects.create_user(**self.user_data)
        otp_record = create_otp_for_user(user)
        
        # Try wrong OTP 3 times
        verify_otp(user, '000000')  # Attempt 1
        verify_otp(user, '000000')  # Attempt 2
        success, message = verify_otp(user, '000000')  # Attempt 3
        
        self.assertFalse(success)
        self.assertIn('Maximum attempts', message)
    
    def test_rate_limiting(self):
        """Test rate limiting on resend"""
        from portal_app.security_utils import resend_otp
        
        user = User.objects.create_user(**self.user_data)
        
        # First OTP
        create_otp_for_user(user)
        
        # Try to resend immediately
        success, message = resend_otp(user)
        
        self.assertFalse(success)
        self.assertIn('wait', message.lower())
```

**Run tests:**
```bash
python manage.py test portal_app.tests.test_otp
```

---

## Troubleshooting

### Common Issues

#### 1. OTP Email Not Received

**Symptoms:**
- User registers but doesn't receive email
- Console shows no email output

**Solutions:**

**Development Mode:**
```python
# Check settings.py
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
- Emails appear in console/terminal
- Check terminal output for OTP code

**Production Mode:**
```bash
# Check email settings in .env
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```
- Verify Gmail App Password is correct
- Check if 2FA is enabled on Google account
- Check spam folder
- Verify email address is correct

**Debug Email Sending:**
```python
# In Django shell
python manage.py shell

from django.core.mail import send_mail
send_mail(
    'Test',
    'Test message',
    'noreply@grampanchayat.gov.in',
    ['test@example.com'],
    fail_silently=False,
)
```

#### 2. OTP Already Expired

**Symptoms:**
- User enters OTP immediately but sees "expired" error

**Solutions:**

1. Check server time:
   ```bash
   date  # Linux/Mac
   echo %date% %time%  # Windows
   ```

2. Ensure timezone is correct in settings.py:
   ```python
   TIME_ZONE = 'Asia/Kolkata'  # Or your timezone
   USE_TZ = True
   ```

3. Check OTP expiration setting:
   ```python
   # In EmailOTP model
   expires_at = timezone.now() + timedelta(minutes=10)
   ```

#### 3. Maximum Attempts Error Immediately

**Symptoms:**
- First attempt shows "maximum attempts exceeded"

**Solutions:**

1. Check if old OTPs exist:
   ```python
   python manage.py shell
   
   from portal_app.models import EmailOTP
   from django.contrib.auth import get_user_model
   
   User = get_user_model()
   user = User.objects.get(username='testuser')
   
   # Check all OTPs
   EmailOTP.objects.filter(user=user)
   
   # Delete old OTPs
   EmailOTP.objects.filter(user=user, is_used=False).delete()
   ```

2. Ensure OTP invalidation works:
   ```python
   # In create_otp_for_user()
   EmailOTP.objects.filter(
       user=user,
       is_verified=False
   ).update(is_used=True)  # Mark old OTPs as used
   ```

#### 4. User Can Login Without Verification

**Symptoms:**
- User skips OTP verification
- Can login without email verification

**Solutions:**

1. Check login view:
   ```python
   def login_view(request):
       # ...
       if not user.email_verified:  # This check is critical
           return redirect('verify_otp')
   ```

2. Check user creation:
   ```python
   def register_view(request):
       user = form.save(commit=False)
       user.is_active = False          # Critical
       user.email_verified = False     # Critical
       user.save()
   ```

3. Verify database:
   ```sql
   SELECT username, email_verified, is_active 
   FROM portal_app_customuser 
   WHERE username = 'testuser';
   ```

#### 5. "No pending verification found" Error

**Symptoms:**
- User redirected to verification page
- Shows "No pending verification found"

**Solutions:**

1. Check session storage:
   ```python
   # In register_view()
   request.session['pending_verification_user_id'] = user.id
   ```

2. Check session middleware:
   ```python
   # In settings.py MIDDLEWARE
   'django.contrib.sessions.middleware.SessionMiddleware',
   ```

3. Clear browser cookies and try again

4. Check session expiry:
   ```python
   # In settings.py
   SESSION_COOKIE_AGE = 3600  # 1 hour
   ```

#### 6. Rate Limiting Not Working

**Symptoms:**
- Can request OTP multiple times per second

**Solutions:**

1. Check resend_otp function:
   ```python
   recent_otp = EmailOTP.objects.filter(
       user=user,
       created_at__gte=timezone.now() - timedelta(minutes=1)
   ).first()
   
   if recent_otp:
       return False, "Please wait 1 minute"
   ```

2. Verify timezone is correct:
   ```python
   USE_TZ = True
   TIME_ZONE = 'Asia/Kolkata'
   ```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Set `DEBUG = False` in settings.py
- [ ] Configure production email backend (SMTP)
- [ ] Set up Gmail App Password or SMTP credentials
- [ ] Test email sending in production environment
- [ ] Configure `.env` file with email settings
- [ ] Set strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Enable HTTPS/SSL
- [ ] Test OTP flow end-to-end
- [ ] Set up email monitoring/logging
- [ ] Configure email rate limits
- [ ] Set up backup email sending service
- [ ] Document email provider credentials securely

### Production Email Configuration

**1. Environment Variables (.env):**

```env
# Django Settings
DEBUG=False
SECRET_KEY=your-very-long-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your-app-password-here
DEFAULT_FROM_EMAIL=Digital Gram Panchayat <noreply@yourdomain.com>

# OTP Settings (optional overrides)
OTP_EXPIRY_MINUTES=10
OTP_MAX_ATTEMPTS=3
```

**2. Settings.py Configuration:**

```python
# Email Backend
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

# Email timeout
EMAIL_TIMEOUT = 10
```

**3. Security Headers:**

```python
# settings.py
if not DEBUG:
    # HTTPS
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

### Email Provider Recommendations

**For Government Portals:**

1. **Google Workspace (Recommended)**
   - Professional email addresses
   - 99.9% uptime SLA
   - Advanced security features
   - Cost: ~$6/user/month

2. **AWS SES**
   - Highly scalable
   - Low cost ($0.10 per 1000 emails)
   - Excellent deliverability
   - Requires AWS account

3. **SendGrid**
   - Free tier: 100 emails/day
   - Easy integration
   - Good analytics
   - Reliable delivery

### Monitoring and Logging

**1. Email Sending Logs:**

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/otp_emails.log',
        },
    },
    'loggers': {
        'portal_app.security_utils': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

**2. Monitor OTP Success Rate:**

```python
# Admin dashboard or management command
from portal_app.models import EmailOTP
from django.utils import timezone
from datetime import timedelta

# Last 24 hours
recent = EmailOTP.objects.filter(
    created_at__gte=timezone.now() - timedelta(days=1)
)

total = recent.count()
verified = recent.filter(is_verified=True).count()
expired = recent.filter(
    is_verified=False,
    expires_at__lt=timezone.now()
).count()

success_rate = (verified / total * 100) if total > 0 else 0
print(f"OTP Success Rate: {success_rate:.2f}%")
print(f"Total OTPs: {total}")
print(f"Verified: {verified}")
print(f"Expired: {expired}")
```

### Database Migration

**Create and apply migrations:**

```bash
# Create migration
python manage.py makemigrations portal_app

# Review migration
python manage.py sqlmigrate portal_app XXXX

# Apply migration
python manage.py migrate

# Verify tables created
python manage.py dbshell
.tables  # SQLite
SHOW TABLES;  # MySQL
```

### Rollback Plan

**If OTP system needs to be disabled:**

1. **Temporary Disable (Quick Fix):**
   ```python
   # In login_view()
   # Comment out email verification check
   # if not user.email_verified:
   #     return redirect('verify_otp')
   ```

2. **Activate All Users:**
   ```python
   python manage.py shell
   
   from django.contrib.auth import get_user_model
   User = get_user_model()
   
   # Activate all users
   User.objects.filter(is_active=False).update(
       is_active=True,
       email_verified=True
   )
   ```

3. **Revert Migration:**
   ```bash
   python manage.py migrate portal_app PREVIOUS_MIGRATION_NUMBER
   ```

---

## Summary

### What Was Implemented

✅ **EmailOTP Model** - Complete OTP tracking system  
✅ **CustomUser Updates** - Email verification fields  
✅ **Security Utils** - OTP generation, verification, email sending  
✅ **Views** - Registration, verification, resend OTP, login checks  
✅ **Forms** - OTP verification form with validation  
✅ **Templates** - Beautiful OTP verification page with timer  
✅ **Email Template** - Professional HTML email  
✅ **URL Routes** - Verification and resend endpoints  
✅ **Admin Interface** - OTP management panel  
✅ **Settings** - Email configuration for dev and production  
✅ **Documentation** - This comprehensive guide  

### Security Compliance

- ✅ Cryptographically secure OTP generation
- ✅ 10-minute expiration
- ✅ Maximum 3 attempts
- ✅ One-time use only
- ✅ Rate limiting (1 per minute)
- ✅ Account inactive until verified
- ✅ Complete security logging
- ✅ CSRF protection
- ✅ Session security
- ✅ Email verification required for login

### Next Steps

1. **Run Migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Test in Development:**
   ```bash
   python manage.py runserver
   # Register new user
   # Check console for OTP
   # Verify email
   ```

3. **Configure Production Email:**
   - Set up Gmail App Password or SMTP
   - Update .env file
   - Test email sending

4. **Deploy to Production:**
   - Follow production deployment checklist
   - Monitor email delivery
   - Track OTP success rates

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review [Testing Guide](#testing-guide)
3. Verify [Email Configuration](#email-configuration)
4. Check Django logs and console output
5. Test email sending separately

---

**Document Version:** 1.0  
**Last Updated:** February 6, 2026  
**Author:** Digital Gram Panchayat Portal Team

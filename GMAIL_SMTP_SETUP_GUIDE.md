# Gmail SMTP Configuration for Django OTP Emails

Complete guide to configure Gmail SMTP for sending OTP verification emails in your Django portal.

---

## 📋 Table of Contents

1. [Current Configuration](#current-configuration)
2. [Gmail App Password Setup](#gmail-app-password-setup)
3. [Environment Configuration](#environment-configuration)
4. [Testing Email Sending](#testing-email-sending)
5. [Troubleshooting](#troubleshooting)
6. [Security Best Practices](#security-best-practices)

---

## ✅ Current Configuration

Your `settings.py` is already configured with:

```python
# Email Backend (Auto-switches based on DEBUG mode)
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Development
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'     # Production

# Gmail SMTP Configuration
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@grampanchayat.gov.in')

# Email Settings
EMAIL_TIMEOUT = 10
EMAIL_SUBJECT_PREFIX = '[Gram Panchayat] '
```

**Key Features:**
- ✅ **Development Mode (DEBUG=True)**: Emails print to console/terminal
- ✅ **Production Mode (DEBUG=False)**: Sends real emails via Gmail SMTP
- ✅ **Secure**: Credentials stored in `.env` file (not in code)
- ✅ **Ready to use**: Just configure `.env` file

---

## 🔐 Gmail App Password Setup

### Step 1: Enable 2-Factor Authentication

1. **Go to Google Account Security:**
   - Visit: https://myaccount.google.com/security
   - Or Google Account → Security

2. **Enable 2-Step Verification:**
   - Click "2-Step Verification"
   - Follow the setup wizard
   - Verify with phone number
   - Complete setup

   **⚠️ Important:** App Passwords are only available with 2FA enabled!

### Step 2: Generate App Password

1. **Access App Passwords:**
   - Visit: https://myaccount.google.com/apppasswords
   - Or Google Account → Security → App Passwords

2. **Create New App Password:**
   ```
   Select App: Mail
   Select Device: Other (Custom name)
   Name: Django Portal OTP System
   ```

3. **Generate Password:**
   - Click "Generate"
   - You'll see a 16-character password like: `abcd efgh ijkl mnop`
   
   **📋 Copy this password immediately!** You won't be able to see it again.

### Step 3: Save Credentials Securely

**DO NOT:**
- ❌ Hardcode password in `settings.py`
- ❌ Commit password to Git
- ❌ Share password publicly

**DO:**
- ✅ Store in `.env` file
- ✅ Add `.env` to `.gitignore`
- ✅ Use environment variables

---

## ⚙️ Environment Configuration

### Create/Update `.env` File

Create or edit `D:\portal\.env` file:

```env
# ============================================
# Django Configuration
# ============================================
DEBUG=False
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# ============================================
# Database Configuration
# ============================================
DB_ENGINE=mysql  # or sqlite
DB_NAME=gram_panchayat_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306

# ============================================
# Gmail SMTP Configuration (OTP Emails)
# ============================================
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True

# Your Gmail address
EMAIL_HOST_USER=your-email@gmail.com

# 16-character App Password (NO SPACES!)
EMAIL_HOST_PASSWORD=abcdefghijklmnop

# From email (can be different from host user)
DEFAULT_FROM_EMAIL=Digital Gram Panchayat <noreply@grampanchayat.gov.in>
```

### Important Notes:

**1. App Password Format:**
```env
# ❌ WRONG (with spaces)
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop

# ✅ CORRECT (no spaces)
EMAIL_HOST_PASSWORD=abcdefghijklmnop
```

**2. Gmail Address:**
```env
# Use your actual Gmail address
EMAIL_HOST_USER=yourname@gmail.com
```

**3. Debug Mode:**
```env
# Development (prints to console)
DEBUG=True

# Production (sends real emails)
DEBUG=False
```

---

## 🧪 Testing Email Sending

### Test 1: Console Backend (Development)

**1. Set DEBUG=True in `.env`:**
```env
DEBUG=True
```

**2. Start server:**
```powershell
python manage.py runserver
```

**3. Register new user:**
- Go to: http://127.0.0.1:8000/register/
- Fill registration form
- Submit

**4. Check console/terminal:**
```
----------------------------------------------------------------------
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Subject: Email Verification OTP - Digital Gram Panchayat Portal
From: noreply@grampanchayat.gov.in
To: user@example.com

Your Verification Code: 123456
This code expires in 10 minutes.
----------------------------------------------------------------------
```

**5. Copy OTP and verify**

### Test 2: Gmail SMTP (Production)

**1. Configure `.env` with Gmail credentials:**
```env
DEBUG=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
```

**2. Test email sending via Django shell:**
```powershell
python manage.py shell
```

```python
# In Django shell:
from django.core.mail import send_mail

# Test email
send_mail(
    subject='Test Email from Django',
    message='This is a test email to verify SMTP configuration.',
    from_email='Digital Gram Panchayat <noreply@grampanchayat.gov.in>',
    recipient_list=['your-email@gmail.com'],  # Your Gmail address
    fail_silently=False,
)

# If successful, you'll see:
# 1
# (This means 1 email was sent successfully)
```

**3. Check your Gmail inbox:**
- Look for email from "Digital Gram Panchayat"
- Subject: "Test Email from Django"
- If received → ✅ Configuration successful!

**4. Test OTP flow:**
```powershell
# Start server
python manage.py runserver

# Register new user
# Go to: http://127.0.0.1:8000/register/
# Use your Gmail address as registration email
# Check your Gmail inbox for OTP
```

### Test 3: Verify OTP System

```powershell
# Test OTP generation
python manage.py shell -c "from portal_app.security_utils import generate_otp; print(f'OTP: {generate_otp()}')"

# Output: OTP: 123456
```

---

## 🐛 Troubleshooting

### Error 1: "SMTPAuthenticationError: Username and Password not accepted"

**Cause:** Wrong email or app password

**Solutions:**

1. **Verify App Password:**
   ```powershell
   # Check .env file
   code .env
   
   # Ensure EMAIL_HOST_PASSWORD has NO SPACES
   # Correct: abcdefghijklmnop
   # Wrong:   abcd efgh ijkl mnop
   ```

2. **Regenerate App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Delete old app password
   - Create new one
   - Update `.env` file

3. **Verify Email Address:**
   ```env
   # Must be your actual Gmail address
   EMAIL_HOST_USER=yourname@gmail.com  # NOT @example.com
   ```

### Error 2: "SMTPServerDisconnected: Connection unexpectedly closed"

**Cause:** Network/firewall blocking port 587

**Solutions:**

1. **Check internet connection**

2. **Test connection:**
   ```powershell
   # Test if port 587 is accessible
   Test-NetConnection -ComputerName smtp.gmail.com -Port 587
   
   # Should show: TcpTestSucceeded: True
   ```

3. **Try port 465 (SSL):**
   ```env
   EMAIL_PORT=465
   EMAIL_USE_TLS=False
   EMAIL_USE_SSL=True
   ```
   
   Update `settings.py`:
   ```python
   EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
   ```

4. **Check firewall/antivirus:**
   - Temporarily disable firewall
   - Test email sending
   - If works, add exception for Python/Django

### Error 3: "SMTPException: STARTTLS extension not supported"

**Cause:** Wrong port or TLS configuration

**Solution:**
```env
# Gmail requires port 587 with TLS
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False  # Don't use SSL on port 587
```

### Error 4: "Email not received" (No errors shown)

**Possible Causes & Solutions:**

1. **Check Spam/Junk Folder:**
   - Gmail might filter emails from new sources
   - Check "Spam" folder
   - Mark as "Not Spam"

2. **Verify Email Address:**
   ```python
   # In registration form, double-check email
   user.email = 'correct-email@gmail.com'
   ```

3. **Check Django logs:**
   ```powershell
   # Run server with verbose logging
   python manage.py runserver --verbosity 3
   ```

4. **Test with different email:**
   - Try different Gmail account
   - Try different email provider (Outlook, Yahoo)

### Error 5: "Please enable 2-Factor Authentication"

**Solution:**
- App Passwords require 2FA
- Go to: https://myaccount.google.com/security
- Enable 2-Step Verification
- Then create App Password

### Error 6: "Connection timed out"

**Solutions:**

1. **Increase timeout:**
   ```python
   # In settings.py
   EMAIL_TIMEOUT = 30  # Increase to 30 seconds
   ```

2. **Check network:**
   ```powershell
   # Ping Gmail SMTP server
   ping smtp.gmail.com
   ```

3. **Use different network:**
   - Try mobile hotspot
   - Some networks block SMTP ports

---

## 🔐 Security Best Practices

### 1. Never Commit Credentials

**Add to `.gitignore`:**
```gitignore
# Environment variables
.env
.env.local
.env.production

# Don't commit database
db.sqlite3
*.sqlite3

# Don't commit uploaded files
media/
uploads/
```

### 2. Use Different Emails for Dev/Prod

```env
# Development
EMAIL_HOST_USER=dev-portal@gmail.com

# Production
EMAIL_HOST_USER=noreply@grampanchayat.gov.in
```

### 3. Rotate App Passwords Regularly

- Change app password every 90 days
- Delete old app passwords
- Generate new ones

### 4. Monitor Email Usage

**Gmail Daily Limits:**
- Free Gmail: **500 emails per day**
- Google Workspace: **2,000 emails per day**

**Track usage:**
```python
# Django shell
from portal_app.models import EmailOTP
from django.utils import timezone
from datetime import timedelta

# Emails sent today
today = timezone.now().date()
count = EmailOTP.objects.filter(
    created_at__date=today
).count()

print(f"OTPs sent today: {count}")
```

### 5. Production Email Service

**For high-volume production, use:**

| Service | Free Tier | Reliability | Setup |
|---------|-----------|-------------|-------|
| **SendGrid** | 100/day | Excellent | Easy |
| **AWS SES** | 62,000/month (first year) | Excellent | Medium |
| **Mailgun** | 5,000/month | Excellent | Easy |
| **Gmail** | 500/day | Good | Very Easy |

**SendGrid Example (.env):**
```env
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
```

---

## 📊 Email Backend Comparison

### Console Backend (Development)

**Pros:**
- ✅ No configuration needed
- ✅ Fast testing
- ✅ No external dependencies
- ✅ No email limits

**Cons:**
- ❌ Emails not actually sent
- ❌ Can't test deliverability
- ❌ Can't test spam filters

**Use for:**
- Local development
- Testing OTP logic
- Quick testing

### Gmail SMTP (Production/Testing)

**Pros:**
- ✅ Real email delivery
- ✅ Free (500/day)
- ✅ Reliable
- ✅ Easy setup

**Cons:**
- ❌ 500 email/day limit
- ❌ Requires App Password
- ❌ Requires 2FA
- ❌ May go to spam initially

**Use for:**
- Small-scale production
- Testing with real emails
- Low-volume portals

---

## 🚀 Quick Reference

### Gmail SMTP Settings

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=16-char-app-password
DEFAULT_FROM_EMAIL=Digital Gram Panchayat <noreply@grampanchayat.gov.in>
```

### Test Commands

```powershell
# Test in Django shell
python manage.py shell

from django.core.mail import send_mail
send_mail('Test', 'Test message', 'from@example.com', ['to@gmail.com'])

# Test OTP generation
from portal_app.security_utils import generate_otp
print(generate_otp())

# Test OTP sending
from portal_app.models import CustomUser
from portal_app.security_utils import create_otp_for_user, send_otp_email

user = CustomUser.objects.get(username='testuser')
otp = create_otp_for_user(user)
send_otp_email(user, otp.otp_code)
```

### Common Issues Quick Fix

```powershell
# Issue: Authentication failed
# Fix: Regenerate App Password and update .env

# Issue: Connection timeout
# Fix: Check internet, try different network

# Issue: Email not received
# Fix: Check spam folder, verify email address

# Issue: Port blocked
# Fix: Try port 465 with SSL instead of 587 with TLS

# Issue: 2FA not enabled
# Fix: Enable 2FA at https://myaccount.google.com/security
```

---

## ✅ Setup Checklist

**Before Using Gmail SMTP:**

- [ ] Gmail account created
- [ ] 2-Factor Authentication enabled
- [ ] App Password generated (16 characters)
- [ ] `.env` file created
- [ ] `EMAIL_HOST_USER` set to your Gmail
- [ ] `EMAIL_HOST_PASSWORD` set to App Password (no spaces)
- [ ] `DEBUG=False` in `.env`
- [ ] `.env` added to `.gitignore`
- [ ] Test email sent successfully
- [ ] OTP email received in Gmail inbox
- [ ] OTP verification tested end-to-end

**Production Deployment:**

- [ ] Use professional email domain (not @gmail.com)
- [ ] Consider SendGrid/AWS SES for high volume
- [ ] Set up email monitoring
- [ ] Configure SPF/DKIM records (if using custom domain)
- [ ] Test spam score
- [ ] Monitor daily email limits

---

## 📞 Support Links

- **Google Account Security:** https://myaccount.google.com/security
- **App Passwords:** https://myaccount.google.com/apppasswords
- **Gmail SMTP Documentation:** https://support.google.com/mail/answer/7126229
- **Django Email Backend:** https://docs.djangoproject.com/en/4.2/topics/email/
- **SendGrid Signup:** https://signup.sendgrid.com/
- **AWS SES:** https://aws.amazon.com/ses/

---

**Last Updated:** February 6, 2026  
**Version:** 1.0  
**Status:** ✅ Production Ready

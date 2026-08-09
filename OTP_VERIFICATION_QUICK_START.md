# OTP System - Quick Setup (5 Minutes)

## ⚡ TL;DR - Start Here

### Step 1: Email Configuration (2 minutes)

**For Gmail (Recommended):**

1. Go to https://myaccount.google.com/apppasswords
2. Select App: **Mail** | Device: **Windows/Linux/Mac**
3. Copy the 16-character password (remove spaces)
4. Create `.env` in project root:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-password
DEFAULT_FROM_EMAIL=your-gmail@gmail.com
```

5. Restart Django:
```bash
# Press Ctrl+C if running
python manage.py runserver
```

---

### Step 2: Test the System (3 minutes)

```bash
# 1. Open browser
http://localhost:8000/register-multi-step/

# 2. Fill and submit form
# → OTP page loads

# 3. Check email inbox for OTP email
# → Subject: "Registration OTP - Digital Gram Panchayat Portal"
# → Copy the 6-digit code

# 4. Paste OTP on page
# → All 6 boxes fill automatically
# → Toast notification appears

# 5. Click "Verify OTP"
# → Success message
# → Redirects to login

# 6. Login with username & password
# → Dashboard loads ✅
```

---

## 🔧 For Development (Console Output)

If you DON'T want to setup Gmail, use console backend:

**Option A: Keep DEBUG=True**
```
- Emails print to Django server console
- No actual email sent
- Perfect for testing
- Current default!
```

**Option B: Explicitly set**
```bash
# In .env:
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Then watch Django console when registering:
```
[OTP EMAIL OUTPUT]
Subject: Registration OTP - Digital Gram Panchayat Portal
To: user@example.com

Your One-Time Password (OTP) is: 482651
```

Copy the OTP from console → paste on web page → verify ✅

---

## 🎯 What Was Fixed

✅ **Strict OTP Enforcement** - User ONLY created after OTP verification
✅ **Premium UI** - Glasmorphism design with animations
✅ **Auto-fill OTP** - Paste detection with all 6 boxes
✅ **Live Timer** - Real-time 10-minute countdown
✅ **Resend with Cooldown** - 60-second rate limiting
✅ **Error Animations** - Shake, color change, retry logic
✅ **Toast Notifications** - Success/error feedback
✅ **Full Validation** - Max attempts, expiry checks
✅ **Keyboard Navigation** - Arrow keys, backspace, enter
✅ **Mobile Responsive** - Works on phones & tablets

---

## 📊 URLs

| Feature | URL | Method |
|---------|-----|--------|
| Register (Multi-step) | `/register-multi-step/` | GET, POST |
| Verify OTP | `/register/verify-otp/` | GET, POST |
| Resend OTP | `/register/resend-otp/` | POST |
| Login | `/login/` | GET, POST |

---

## 🔒 Security Features

- ✅ OTP hashing (not stored in plain text)
- ✅ 10-minute expiry (configurable)
- ✅ 3 attempt limit per OTP
- ✅ 60-second rate limiting on resend
- ✅ Session-based flow (no direct access)
- ✅ CSRF protection on all forms
- ✅ Email verification flag on user account

---

## 🐛 Common Issues & Fixes

| Problem | Solution |
|---------|----------|
| OTP not sending | Check `.env` has EMAIL_HOST_USER & PASSWORD |
| OTP invalid | Use MOST RECENT OTP from email, not old one |
| Timer frozen | Refresh page (F5) |
| "Max attempts" | Click "Resend OTP" button |
| "OTP expired" | Still click "Resend OTP" to get new one |
| Session expired | Re-register from `/register-multi-step/` |

---

## 📧 Email Templates

The email sent to users contains:
```
From: noreply@grampanchayat.gov.in
Subject: Registration OTP - Digital Gram Panchayat Portal

Dear [User Name],

Thank you for registering with Digital Gram Panchayat Portal.
Your One-Time Password (OTP) is: [6-DIGIT CODE]

This OTP is valid for 10 minutes. Do not share it with anyone.

Regards,
Digital Gram Panchayat Portal
```

---

## 🧪 Quick Test Checklist

```
□ Registration form loads at /register-multi-step/
□ OTP page loads after form submission
□ Email received with OTP code
□ OTP auto-fills when pasted
□ Timer counts down from 10:00
□ Verify button enabled when 6 digits filled
□ Invalid OTP shows error + shake
□ Valid OTP creates account + redirects to login
□ Can login with username/password
□ Dashboard loads
```

---

## ⚙️ Configuration Files

**What was created/modified:**

| File | Purpose |
|------|---------|
| `otp-verification-premium.html` | OTP input template (premium UI) |
| `otp-verification-premium.css` | Glasmorphism, animations, responsive |
| `otp-verification-premium.js` | OTP input logic, timer, resend |
| `views.py` (modified) | Fixed template name + time context |
| `OTP_VERIFICATION_COMPLETE_GUIDE.md` | Full documentation (this whole repo) |

---

## 🚀 Next Steps for Production

1. **Email Service:**
   ```bash
   # Use Gmail, AWS SES, SendGrid, or Mailgun
   # All need EMAIL_HOST_USER & PASSWORD in .env
   ```

2. **Test Thoroughly:**
   ```bash
   # Register multiple test accounts
   # Test with invalid OTPs
   # Test resend functionality
   # Test on mobile devices
   ```

3. **Deploy:**
   ```bash
   # Set DEBUG = False in settings.py
   # Run migrations: python manage.py migrate
   # Collect static files: python manage.py collectstatic
   # Use production email service (not Gmail)
   ```

4. **Monitor:**
   ```bash
   # Check email delivery logs
   # Monitor failed registrations
   # Review error logs regularly
   ```

---

## 📞 Support

If something doesn't work:

1. **Check .env file** - Email configuration is missing or wrong
2. **Check Django Console** - For email output (in DEBUG mode)
3. **Read Complete Guide** - `OTP_VERIFICATION_COMPLETE_GUIDE.md`
4. **Database Query** - Check if PendingRegistration was created
5. **Browser Console** - F12 → Console for JavaScript errors

---

**Ready to test?** Start at Step 1 above! 🎉

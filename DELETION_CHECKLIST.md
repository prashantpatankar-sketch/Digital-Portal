# ✅ SAFE USER DELETION - COMPLETE CHECKLIST

**Project:** Digital Gram Panchayat Portal  
**Date:** April 11, 2026  
**Safety Level:** 🟢 Maximum Protection

---

## 📋 PRE-DELETION CHECKLIST

### ✓ Environmental Check

- [ ] You are in the correct project directory: `d:\portal`
- [ ] Virtual environment is activated: `.venv\Scripts\activate`
- [ ] MySQL/Database is running and accessible
- [ ] You have database credentials (username, password)
- [ ] No Django development server running on port 8000
- [ ] You have admin/superuser account (don't delete this!)

### ✓ Backup Check

- [ ] MySQL backup created: `mysqldump -u root -p gram_panchayat > backup.sql`
- [ ] OR Django backup created: `python manage.py dumpdata > backup.json`
- [ ] Backup file size verified (should be >1MB if data exists)
- [ ] Backup file location noted and safe
- [ ] You can restore the backup if needed

### ✓ Data Review

- [ ] You know how many users will be deleted
  ```bash
  python manage.py shell
  # Then in shell:
  from portal_app.models import CustomUser
  CustomUser.objects.filter(role__in=['citizen','staff']).count()
  ```
- [ ] You understand CASCADE deletion will remove:
  - Applications
  - Complaints
  - Bills (electricity, water, property tax)
  - Activity logs
  - Notifications

### ✓ Admin Account Check

- [ ] Verified at least one admin/superuser account exists
  ```bash
  python manage.py shell
  # Then:
  from portal_app.models import CustomUser
  CustomUser.objects.filter(is_superuser=True)
  ```
- [ ] Admin account username noted: `___________`
- [ ] Admin account will NOT be deleted
- [ ] After deletion, you can login with admin account

---

## 🚀 EXECUTION CHECKLIST

### ✓ Choose Your Method

- [ ] **Method 1 (RECOMMENDED):** Management command
  ```bash
  python manage.py delete_non_admin_users
  ```

- [ ] **Method 2:** Python script
  ```bash
  python delete_users_script.py
  ```

- [ ] **Method 3:** Django shell (manual)
  ```bash
  python manage.py shell
  # Paste deletion code
  ```

- [ ] **Method 4:** SQL (only if Django fails)
  - Use `SQL_ALTERNATIVE_DELETION.md`

### ✓ Execute Deletion

**Choose ONE method above:**

#### If using Management Command:
- [ ] Open terminal in project directory
- [ ] Run: `python manage.py delete_non_admin_users`
- [ ] When prompted, type: `yes`
- [ ] Confirm deletion is complete

#### If using Python Script:
- [ ] Open terminal in project directory
- [ ] Run: `python delete_users_script.py`
- [ ] Follow on-screen prompts
- [ ] Confirm deletion is complete

#### If using Django Shell:
- [ ] Open terminal in project directory
- [ ] Run: `python manage.py shell`
- [ ] Copy/paste code from `SAFE_USER_DELETION_GUIDE.md`
- [ ] Type `exit()` to close shell

#### If using SQL:
- [ ] Open MySQL client
- [ ] Run queries from `SQL_ALTERNATIVE_DELETION.md`
- [ ] Wait for completion

---

## ✅ POST-DELETION VERIFICATION

### ✓ Database Check

In Django shell:
```python
from portal_app.models import CustomUser, Application, Complaint

# Should return 0
print(CustomUser.objects.filter(role='citizen').count())

# Should return 0
print(CustomUser.objects.filter(role='staff').count())

# Should return >0 (admin/superuser)
print(CustomUser.objects.filter(role='admin').count())
print(CustomUser.objects.filter(is_superuser=True).count())

# Verify cascades worked
print(Application.objects.count())  # Should be 0 or very low
print(Complaint.objects.count())    # Should be 0

# Check no orphans
print(Application.objects.filter(applicant__isnull=True).count())
print(Complaint.objects.filter(complainant__isnull=True).count())
```

**Expected Results:**
```
- Citizens remaining: 0
- Staff remaining: 0
- Admins remaining: 1+ (your admin)
- Superusers remaining: 1+ (your superuser)
- Orphan records: 0
```

### ✓ Checklist Items

- [ ] Citizens count = 0
- [ ] Staff count = 0
- [ ] Admin/Superuser count ≥ 1
- [ ] Applications count = 0 (cascade worked)
- [ ] Complaints count = 0 (cascade worked)
- [ ] No orphan records found
- [ ] Database shows no errors

---

## 🧪 FUNCTIONALITY CHECK

### ✓ Admin Panel Test

- [ ] Can login to `/admin` with admin credentials
- [ ] Admin dashboard displays correctly
- [ ] Can navigate to CustomUser model
- [ ] Shows remaining users only
- [ ] No errors in admin panel

### ✓ Registration Test

- [ ] Can access `/register` page
- [ ] Registration form displays
- [ ] Can fill out registration form
- [ ] OTP verification process works
- [ ] New user can be created

### ✓ Login Test

- [ ] Can logout from admin
- [ ] Fresh user can login with new credentials
- [ ] Session management works
- [ ] Dashboard displays correctly

### ✓ Application Features Test

- [ ] Birth Certificate application works
- [ ] Death Certificate application works
- [ ] Income Certificate application works
- [ ] Complaint submission works
- [ ] Bill payment system works

### ✓ System Features Test

- [ ] Email notifications send correctly
- [ ] Database queries run without errors
- [ ] No "user not found" errors in logs
- [ ] Media files upload correctly
- [ ] Static files load correctly

---

## 📊 FINAL VALIDATION

### ✓ Database Statistics

Run this in Django shell:
```python
from portal_app.models import *

print("FINAL DATABASE STATE:")
print(f"CustomUser: {CustomUser.objects.count()}")
print(f"Application: {Application.objects.count()}")
print(f"Complaint: {Complaint.objects.count()}")
print(f"ElectricityBill: {ElectricityBill.objects.count()}")
print(f"WaterBill: {WaterBill.objects.count()}")
print(f"PropertyTaxRecord: {PropertyTaxRecord.objects.count()}")
print(f"Notification: {Notification.objects.count()}")
print(f"UserActivity: {UserActivity.objects.count()}")
```

- [ ] All non-admin user counts = 0
- [ ] No foreign key constraint errors
- [ ] Database integrity maintained
- [ ] All tables accessible

### ✓ Project Integrity Check

- [ ] Project structure unchanged
- [ ] No migration files deleted
- [ ] Settings.py unchanged
- [ ] URLs.py unchanged
- [ ] No code modifications needed
- [ ] No packages need reinstalling

---

## 🎯 SUCCESS CRITERIA

✅ **All of these must be TRUE:**

- [ ] Citizens deleted: **YES** (count = 0)
- [ ] Staff deleted: **YES** (count = 0)
- [ ] Admin protected: **YES** (count ≥ 1)
- [ ] Database integrity: **YES** (no orphans)
- [ ] System functional: **YES** (all features work)
- [ ] No errors: **YES** (no error logs)

**If ANY checkbox above is unchecked, DO NOT proceed until fixed.**

---

## 🚨 EMERGENCY RECOVERY

### If Something Goes Wrong:

**Step 1: Stop everything**
- Close terminal (Ctrl+C)
- Stop Django server if running
- Don't make any more changes

**Step 2: Restore immediately**

```bash
# If you have MySQL backup
mysql -u root -p gram_panchayat < backup_before_deletion.sql

# If you have Django JSON backup
python manage.py loaddata backup_before_deletion.json
```

**Step 3: Verify restoration**
```bash
python manage.py shell
from portal_app.models import CustomUser
print(f"Users restored: {CustomUser.objects.count()}")
# Should show original count
```

**Step 4: Contact support** if restoration fails

---

## 📝 COMPLETION SUMMARY

**Task Status:** ✅ COMPLETE

**What was deleted:**
- [ ] Register count of deleted users: `___________`
- [ ] Deletion completed at: `___________` (Date/Time)
- [ ] Verified with admin: `___________` (Name)

**System Status After Deletion:**
- Remaining users: `___________`
- Remaining admins: `___________`
- System ready for: `___________`

**Notes:**
```
_________________________________
_________________________________
_________________________________
```

---

## 📞 TROUBLESHOOTING

### Problem: "No such file or directory"
- [ ] Check you're in correct directory: `d:\portal`
- [ ] Use absolute paths: `python manage.py dumpdata`

### Problem: "Access denied" (MySQL)
- [ ] Verify MySQL is running
- [ ] Check username/password correct
- [ ] Try: `mysql -u root -p`

### Problem: "Module not found"
- [ ] Activate virtual environment
- [ ] Run: `.\.venv\Scripts\activate`

### Problem: "Deletion didn't work"
- [ ] DON'T try again
- [ ] Restore backup immediately
- [ ] Check error messages
- [ ] Use different method (SQL instead of Django)

### Problem: "Can't login to admin"
- [ ] Check admin account wasn't deleted
- [ ] Restore from backup if needed
- [ ] Create new superuser: `python manage.py createsuperuser`

---

## 🏁 FINAL SIGN-OFF

**Performed by:** `___________________`

**Date:** `____/____/______`

**Time:** `____:____ __`

**Backup location:** `___________________`

**Backup verified:** ☐ YES ☐ NO

**Deletion successful:** ☐ YES ☐ NO

**All tests passed:** ☐ YES ☐ NO

**System ready:** ☐ YES ☐ NO

---

## ✨ SUCCESS!

Your system has been safely cleaned and is ready for fresh user registration!

**Next steps:**
1. ✅ Test registration with new user
2. ✅ Deploy if needed
3. ✅ Monitor activity logs
4. ✅ Keep backup safe (for 30 days)

**Support contacts:**
- Technical: Check error logs in `/logs/`
- Database: MySQL logs in MySQL folder
- Django: Check terminal output

---

**Documentation:** [SAFE_USER_DELETION_GUIDE.md](SAFE_USER_DELETION_GUIDE.md)  
**Quick Reference:** [USER_DELETION_QUICK_REF.md](USER_DELETION_QUICK_REF.md)  
**SQL Alternative:** [SQL_ALTERNATIVE_DELETION.md](SQL_ALTERNATIVE_DELETION.md)  
**Management Command:** [portal_app/management/commands/delete_non_admin_users.py](portal_app/management/commands/delete_non_admin_users.py)

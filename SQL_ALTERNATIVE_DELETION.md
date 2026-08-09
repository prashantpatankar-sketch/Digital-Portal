# Safe User Deletion - SQL Alternative

**ONLY USE IF DJANGO ORM FAILS** - Django ORM is the preferred method.

---

## 🔒 BACKUP FIRST (CRITICAL)

### MySQL Backup

```bash
# Windows Command Prompt or PowerShell
mysqldump -u root -p gram_panchayat > "C:\backup_before_deletion.sql"

# When prompted, enter your MySQL password
```

### Verify Backup

```bash
# Check file size (should be several MB if has data)
dir C:\backup_before_deletion.sql
```

---

## 📊 COUNT BEFORE DELETION

Connect to MySQL:

```bash
mysql -u root -p gram_panchayat
```

Then run:

```sql
-- Count users by role
SELECT role, COUNT(*) as count FROM portal_app_customuser GROUP BY role;

-- Count users to delete
SELECT COUNT(*) as total_to_delete FROM portal_app_customuser 
WHERE role IN ('citizen', 'staff') AND is_superuser = 0;

-- Count related data
SELECT 'Applications' as table_name, COUNT(*) as count FROM portal_app_application
WHERE applicant_id IN (
    SELECT id FROM portal_app_customuser 
    WHERE role IN ('citizen', 'staff') AND is_superuser = 0
)
UNION ALL
SELECT 'Complaints', COUNT(*) FROM portal_app_complaint
WHERE complainant_id IN (
    SELECT id FROM portal_app_customuser 
    WHERE role IN ('citizen', 'staff') AND is_superuser = 0
);
```

---

## ⚠️ CRITICAL: Before Running DELETE

**DOUBLE-CHECK THESE:**

```sql
-- Verify admins are protected
SELECT id, username, role, is_superuser FROM portal_app_customuser 
WHERE role = 'admin' OR is_superuser = 1;

-- Remember: DON'T delete these users!
```

---

## 🗑️ DELETION SQL (Use with Extreme Caution)

**Method 1: Simple (if NO custom on_delete settings)**

```sql
-- DELETE users (triggers CASCADE for related tables)
DELETE FROM portal_app_customuser 
WHERE role IN ('citizen', 'staff') 
AND is_superuser = 0;
```

**Method 2: Explicit Cascade (SAFER)**

The following order ensures proper cascade:

```sql
-- 1. Delete application status history first
DELETE FROM portal_app_applicationstatushistory 
WHERE application_id IN (
    SELECT id FROM portal_app_application 
    WHERE applicant_id IN (
        SELECT id FROM portal_app_customuser 
        WHERE role IN ('citizen', 'staff') AND is_superuser = 0
    )
);

-- 2. Delete related certificate records
DELETE FROM portal_app_birthcertificate 
WHERE application_id IN (
    SELECT id FROM portal_app_application 
    WHERE applicant_id IN (
        SELECT id FROM portal_app_customuser 
        WHERE role IN ('citizen', 'staff') AND is_superuser = 0
    )
);

DELETE FROM portal_app_deathcertificate 
WHERE application_id IN (
    SELECT id FROM portal_app_application 
    WHERE applicant_id IN (
        SELECT id FROM portal_app_customuser 
        WHERE role IN ('citizen', 'staff') AND is_superuser = 0
    )
);

DELETE FROM portal_app_incomecertificate 
WHERE application_id IN (
    SELECT id FROM portal_app_application 
    WHERE applicant_id IN (
        SELECT id FROM portal_app_customuser 
        WHERE role IN ('citizen', 'staff') AND is_superuser = 0
    )
);

-- 3. Delete bill requests
DELETE FROM portal_app_billrequest 
WHERE application_id IN (
    SELECT id FROM portal_app_application 
    WHERE applicant_id IN (
        SELECT id FROM portal_app_customuser 
        WHERE role IN ('citizen', 'staff') AND is_superuser = 0
    )
);

-- 4. Delete tax payments
DELETE FROM portal_app_taxpayment 
WHERE application_id IN (
    SELECT id FROM portal_app_application 
    WHERE applicant_id IN (
        SELECT id FROM portal_app_customuser 
        WHERE role IN ('citizen', 'staff') AND is_superuser = 0
    )
);

-- 5. Delete applications
DELETE FROM portal_app_application 
WHERE applicant_id IN (
    SELECT id FROM portal_app_customuser 
    WHERE role IN ('citizen', 'staff') AND is_superuser = 0
);

-- 6. Delete complaint history
DELETE FROM portal_app_complainthistory 
WHERE complaint_id IN (
    SELECT id FROM portal_app_complaint 
    WHERE complainant_id IN (
        SELECT id FROM portal_app_customuser 
        WHERE role IN ('citizen', 'staff') AND is_superuser = 0
    )
);

-- 7. Delete complaints
DELETE FROM portal_app_complaint 
WHERE complainant_id IN (
    SELECT id FROM portal_app_customuser 
    WHERE role IN ('citizen', 'staff') AND is_superuser = 0
);

-- 8. Delete bills
DELETE FROM portal_app_electricitybill 
WHERE user_id IN (
    SELECT id FROM portal_app_customuser 
    WHERE role IN ('citizen', 'staff') AND is_superuser = 0
);

DELETE FROM portal_app_waterbill 
WHERE user_id IN (
    SELECT id FROM portal_app_customuser 
    WHERE role IN ('citizen', 'staff') AND is_superuser = 0
);

DELETE FROM portal_app_propertytaxrecord 
WHERE user_id IN (
    SELECT id FROM portal_app_customuser 
    WHERE role IN ('citizen', 'staff') AND is_superuser = 0
);

-- 9. Delete notifications and activity logs
DELETE FROM portal_app_notification 
WHERE recipient_id IN (
    SELECT id FROM portal_app_customuser 
    WHERE role IN ('citizen', 'staff') AND is_superuser = 0
);

DELETE FROM portal_app_useractivity 
WHERE user_id IN (
    SELECT id FROM portal_app_customuser 
    WHERE role IN ('citizen', 'staff') AND is_superuser = 0
);

-- 10. Delete pending registrations
DELETE FROM portal_app_pendingregistration;

-- 11. Finally, delete users
DELETE FROM portal_app_customuser 
WHERE role IN ('citizen', 'staff') 
AND is_superuser = 0;

-- ✓ COMMITTED - All data deleted
```

---

## ✅ VERIFY DELETION

```sql
-- Check remaining users
SELECT COUNT(*) as total_users FROM portal_app_customuser;
SELECT role, COUNT(*) FROM portal_app_customuser GROUP BY role;

-- Verify no citizens/staff remain
SELECT COUNT(*) as citizen_staff_remaining FROM portal_app_customuser 
WHERE role IN ('citizen', 'staff') AND is_superuser = 0;

-- Verify admins safe
SELECT id, username, role FROM portal_app_customuser 
WHERE role = 'admin' OR is_superuser = 1;

-- Check related data counts
SELECT 'Applications' as table_name, COUNT(*) as count FROM portal_app_application
UNION ALL
SELECT 'Complaints', COUNT(*) FROM portal_app_complaint
UNION ALL
SELECT 'Electricity Bills', COUNT(*) FROM portal_app_electricitybill
UNION ALL
SELECT 'Water Bills', COUNT(*) FROM portal_app_waterbill
UNION ALL
SELECT 'Property Tax', COUNT(*) FROM portal_app_propertytaxrecord;
```

---

## 🔄 RESTORE IF SOMETHING GOES WRONG

**IMMEDIATELY restore from backup:**

```bash
# If deletion goes wrong, restore backup ASAP
mysql -u root -p gram_panchayat < C:\backup_before_deletion.sql

# When prompted, confirm you want to restore
```

---

## ⚰️ IMPORTANT WARNINGS

1. **BACKUP FIRST** - Cannot recover without backup
2. **NO UNDO** - This is permanent
3. **ADMIN SAFE** - Double-check the WHERE clause
4. **CASCADE RISK** - Only use if Django fails
5. **TEST FIRST** - Run SELECT queries first to verify count

---

## 🎯 Recommended Approach

**DO NOT use raw SQL unless Django ORM fails.**

Instead:
1. ✅ Try Django ORM method first (safest)
2. ⚠️ Only use SQL if Django ORM fails
3. 🔒 Always backup first
4. ✓ Verify before/after counts
5. 🔄 Restore if any issues

---

## 💡 FAQ

**Q: Will this break foreign keys?**  
A: No, if you follow the deletion order above

**Q: Can I run this in one transaction?**  
A: Yes, wrap in `START TRANSACTION; ... COMMIT;`

**Q: What if deletion hangs?**  
A: Press Ctrl+C, restore backup, try Django ORM instead

**Q: Do I need to run migrations?**  
A: No, only deleting data, not changing schema

---

## 🚀 Safe SQL Deletion Template

Save as `delete_users_safe.sql`:

```sql
-- SAFE USER DELETION SCRIPT
-- Date: 2026-04-11
-- Change these to your database name and table prefix

-- BACKUP FIRST!
-- mysqldump -u root -p gram_panchayat > backup.sql

START TRANSACTION;

-- Delete in cascade order
DELETE FROM portal_app_applicationstatushistory WHERE id > 0;
DELETE FROM portal_app_birthcertificate WHERE id > 0;
DELETE FROM portal_app_deathcertificate WHERE id > 0;
DELETE FROM portal_app_incomecertificate WHERE id > 0;
DELETE FROM portal_app_billrequest WHERE id > 0;
DELETE FROM portal_app_taxpayment WHERE id > 0;
DELETE FROM portal_app_application WHERE applicant_id NOT IN (
    SELECT id FROM portal_app_customuser WHERE role = 'admin'
);
DELETE FROM portal_app_complainthistory WHERE id > 0;
DELETE FROM portal_app_complaint WHERE complainant_id NOT IN (
    SELECT id FROM portal_app_customuser WHERE role = 'admin'
);
DELETE FROM portal_app_electricitybill WHERE user_id NOT IN (
    SELECT id FROM portal_app_customuser WHERE role = 'admin'
);
DELETE FROM portal_app_waterbill WHERE user_id NOT IN (
    SELECT id FROM portal_app_customuser WHERE role = 'admin'
);
DELETE FROM portal_app_propertytaxrecord WHERE user_id NOT IN (
    SELECT id FROM portal_app_customuser WHERE role = 'admin'
);
DELETE FROM portal_app_notification WHERE recipient_id NOT IN (
    SELECT id FROM portal_app_customuser WHERE role = 'admin'
);
DELETE FROM portal_app_useractivity WHERE user_id NOT IN (
    SELECT id FROM portal_app_customuser WHERE role = 'admin'
);
DELETE FROM portal_app_customuser WHERE role IN ('citizen', 'staff') AND is_superuser = 0;

COMMIT;

-- Verify
SELECT COUNT(*) as remaining_users FROM portal_app_customuser;
```

Run with:
```bash
mysql -u root -p gram_panchayat < delete_users_safe.sql
```

---

**⚠️ AGAIN: Django ORM is safer. Use SQL only as last resort.**

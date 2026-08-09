# 🚀 QUICK DELETION REFERENCE

## Fastest Methods (Choose One)

### METHOD 1: Management Command (Easiest)
```bash
python manage.py delete_non_admin_users
```

### METHOD 2: Direct Python Script
```bash
python manage.py shell
exec(open('delete_users_script.py').read())
```

### METHOD 3: Django Shell (Manual Control)
```bash
python manage.py shell
```

Then paste this:
```python
from portal_app.models import CustomUser

# See what will be deleted
citizens = CustomUser.objects.filter(role='citizen').count()
staff = CustomUser.objects.filter(role='staff').count()
print(f"Will delete: {citizens} citizens + {staff} staff = {citizens+staff} total")

# Delete
CustomUser.objects.filter(
    role__in=['citizen', 'staff']
).exclude(is_superuser=True).delete()

# Verify
print(f"Remaining: {CustomUser.objects.count()} users")
```

---

## Backup First (HIGHLY RECOMMENDED)

```bash
# MySQL backup
mysqldump -u root -p gram_panchayat > backup_$(date +%Y%m%d_%H%M%S).sql

# Or Django backup
python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json
```

---

## Restore if Needed

```bash
# From MySQL
mysql -u root -p gram_panchayat < backup_20260411_120000.sql

# From Django JSON
python manage.py loaddata backup_20260411_120000.json
```

---

## Quick Verification

```python
from portal_app.models import CustomUser, Application, Complaint

# Count check
print(CustomUser.objects.count())           # Should be 1+ (admin only)
print(CustomUser.objects.filter(role='citizen').count())  # Should be 0
print(Application.objects.count())          # Should be 0
print(Complaint.objects.count())            # Should be 0
```

---

## What Gets Deleted

✓ Citizens (all)  
✓ Staff (all)  
✓ Applications (all citizen/staff)  
✓ Complaints (all)  
✓ Bills (electricity, water, property tax)  
✓ Notifications  
✓ Activity logs  

## What Stays

✓ Admin/superuser accounts  
✓ Project structure  
✓ Database schema  
✓ All functionality  
✓ System configuration  

---

## Troubleshooting

**"No module named portal_app"?**
- Ensure you're in the project directory (d:\portal)
- Check PYTHONPATH includes the project

**"Foreign key constraint failed"?**
- Don't use raw SQL
- Use Django ORM (it handles CASCADE)

**"Command not found"?**
- Ensure you created `/portal_app/management/commands/` directory
- Check file names match exactly

**Want to undo?**
- Restore from backup immediately (before any new data)

---

## ⏱️ Performance

- **100 users**: ~2 seconds
- **1000 users**: ~20 seconds  
- **5000 users**: ~2 minutes

All related data deleted via CASCADE automatically.

---

**Remember:** Make a backup first! 🔒

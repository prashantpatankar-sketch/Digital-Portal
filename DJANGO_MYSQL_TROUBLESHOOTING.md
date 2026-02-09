# 🔧 Django + MySQL Troubleshooting Guide

## Quick Reference: Connection Issues

### Symptom 1: "No module named MySQLdb"

```
Error: ModuleNotFoundError: No module named 'MySQLdb'
```

**Checklist:**
- [ ] Is virtual environment activated? (prompt shows `(venv)`)
- [ ] Is mysqlclient installed? `pip list | grep mysqlclient`
- [ ] Do you have Visual C++ Build Tools?

**Solutions (in order):**

```bash
# 1. Try installing mysqlclient
pip install mysqlclient==2.2.1

# If that fails with build error:
# 2. Install Visual C++ Build Tools
#    https://visualstudio.microsoft.com/downloads/
#    Select: Desktop Development with C++
#    Then retry: pip install mysqlclient

# If still fails:
# 3. Use mysql-connector-python instead
pip uninstall mysqlclient
pip install mysql-connector-python
```

---

### Symptom 2: MySQL Server Not Responding

```
Error: (2003, "Can't connect to MySQL server on '127.0.0.1:3306'")
Error: (10061, "No connection could be made because the target machine actively refused it")
```

**Checklist:**
- [ ] Is MySQL service running?
- [ ] Is port 3306 available?
- [ ] Is firewall blocking MySQL?

**Solutions:**

```bash
# 1. Check if MySQL is running
Get-Service MySQL80
# Should show: Running

# 2. If not running, start it
Start-Service MySQL80

# 3. Verify connection manually
mysql -u root -p
# Enter password
# If successful, you'll see: mysql>

# 4. Check if port is in use
netstat -ano | findstr 3306
# Should show MySQL process using port 3306

# 5. Restart MySQL service
Restart-Service MySQL80
```

---

### Symptom 3: "Access Denied" Error

```
Error: (1045, "Access denied for user 'django_user'@'localhost'")
```

**Checklist:**
- [ ] Username correct in settings.py?
- [ ] Password correct in settings.py?
- [ ] User exists in MySQL?
- [ ] User has privileges on database?

**Solutions:**

```bash
# 1. Verify credentials manually
mysql -u django_user -p gram_panchayat_db
# If fails, problem is with credentials

# 2. Login as root
mysql -u root -p
# Enter root password

# 3. Check if user exists
SELECT User, Host FROM mysql.user WHERE User='django_user';

# 4. If user doesn't exist, create it
CREATE USER 'django_user'@'localhost' IDENTIFIED BY 'your_password';

# 5. Grant privileges
GRANT ALL PRIVILEGES ON gram_panchayat_db.* TO 'django_user'@'localhost';
FLUSH PRIVILEGES;

# 6. Verify
SELECT User, Host FROM mysql.user WHERE User='django_user';

# Exit
EXIT;

# 7. Test again with Django
mysql -u django_user -p gram_panchayat_db
```

**Update settings.py:**
```python
'USER': 'django_user',
'PASSWORD': 'your_password',  # Must match!
```

---

### Symptom 4: "Database Does Not Exist"

```
Error: (1049, "Unknown database 'gram_panchayat_db'")
```

**Checklist:**
- [ ] Database exists in MySQL?
- [ ] Database name matches settings.py?
- [ ] Spelling correct?

**Solutions:**

```bash
# 1. Login to MySQL
mysql -u root -p

# 2. List all databases
SHOW DATABASES;
# Look for: gram_panchayat_db

# 3. If not found, create it
CREATE DATABASE gram_panchayat_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 4. Verify
SHOW DATABASES;

# Exit
EXIT;

# 5. Update Django settings.py
# Make sure NAME matches exactly:
'NAME': 'gram_panchayat_db',
```

---

### Symptom 5: Migrations Not Applying

```
Error: django.db.utils.OperationalError: (1030, "Got error 28 from storage engine")
```

**Checklist:**
- [ ] Database has enough disk space?
- [ ] MySQL has proper permissions?
- [ ] Database charset correct?

**Solutions:**

```bash
# 1. Check disk space
# Ensure you have >1GB free space

# 2. Fix charset and sql_mode
mysql -u root -p gram_panchayat_db
ALTER DATABASE gram_panchayat_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;

# 3. In settings.py, add OPTIONS
'OPTIONS': {
    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    'charset': 'utf8mb4',
}

# 4. Re-run migrations
python manage.py migrate
```

---

### Symptom 6: "Lost Connection to MySQL"

```
Error: (2006, 'MySQL server has gone away')
Error: (2013, 'Lost connection to MySQL server during query')
```

**Checklist:**
- [ ] MySQL process still running?
- [ ] Connection timeout set?
- [ ] Network stability?

**Solutions:**

```bash
# 1. Restart MySQL
Restart-Service MySQL80

# 2. Add timeout setting to settings.py
'CONN_MAX_AGE': 600,  # 10 minutes

# 3. Check MySQL max connections
mysql -u root -p
SHOW VARIABLES LIKE 'max_connections';
# If <100, increase it:
SET GLOBAL max_connections = 1000;
EXIT;

# 4. Restart Django server
python manage.py runserver
```

---

### Symptom 7: Charset/Encoding Errors

```
Error: "You must use the 'encoding' option or 'charset' option"
Error: UnicodeDecodeError: 'utf-8' codec can't decode byte
```

**Checklist:**
- [ ] Database charset is utf8mb4?
- [ ] Table charset is utf8mb4?
- [ ] Django OPTIONS configured?

**Solutions:**

```bash
# 1. Login to MySQL
mysql -u root -p gram_panchayat_db

# 2. Check database charset
SHOW CREATE DATABASE gram_panchayat_db;
# Should show: CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci

# 3. Fix if needed
ALTER DATABASE gram_panchayat_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 4. Check all tables
SHOW CREATE TABLE auth_user;
# Should show: CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci

# 5. Exit
EXIT;

# 6. Update settings.py
'OPTIONS': {
    'charset': 'utf8mb4',
    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
}

# 7. Re-run migrations
python manage.py migrate
```

---

### Symptom 8: "Host is not allowed to connect"

```
Error: (1130, "Host '127.0.0.1' is not allowed to connect to this MySQL server")
```

**Checklist:**
- [ ] User privileges set for correct host?
- [ ] Using correct host in settings.py?

**Solutions:**

```bash
# 1. Login as root
mysql -u root -p

# 2. Check user host configuration
SELECT User, Host FROM mysql.user WHERE User='django_user';

# 3. If Host is not 'localhost' or '%', fix it
DROP USER 'django_user'@'old_host';

# 4. Create user with correct host
CREATE USER 'django_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON gram_panchayat_db.* TO 'django_user'@'localhost';
FLUSH PRIVILEGES;

# Exit
EXIT;

# 5. Update settings.py if needed
'HOST': '127.0.0.1',  # or 'localhost'
```

---

### Symptom 9: "Table Already Exists"

```
Error: (1050, "Table 'django_migrations' already exists")
```

**Checklist:**
- [ ] Migration already applied?
- [ ] Multiple Django instances running?

**Solutions:**

```bash
# 1. Check migration status
python manage.py migrate --list

# 2. If migrations are marked as applied, skip them
python manage.py migrate --fake

# 3. If you need to reset:
# ⚠️ THIS DELETES ALL DATA!
python manage.py flush --no-input

# 4. Re-apply migrations
python manage.py migrate

# 5. Create new superuser
python manage.py createsuperuser
```

---

## Diagnostic Checklist

### When Migration Fails

Run this step-by-step:

```bash
# Step 1: Verify MySQL is running
Get-Service MySQL80
# Status: Running? YES ✓ / NO ✗

# Step 2: Test connection to database
mysql -u django_user -p gram_panchayat_db
# Can login? YES ✓ / NO ✗
# If NO, fix credentials

# Step 3: Check Django can connect
python manage.py shell
>>> from django.db import connection
>>> connection.ensure_connection()
>>> exit()
# No errors? YES ✓ / NO ✗

# Step 4: Try migration again
python manage.py migrate --verbosity=2
# Helpful output with details
```

---

### When Admin Page Not Working

```bash
# Step 1: Is server running?
python manage.py runserver
# See: Starting development server? YES ✓

# Step 2: Go to admin page
# http://127.0.0.1:8000/admin/

# Step 3: Check for errors
# Look at terminal window where server runs
# Any red error messages? YES ✓ = Problem

# Step 4: Check if superuser exists
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(is_superuser=True).exists()
# Should print: True

# Step 5: If no superuser
>>> exit()
python manage.py createsuperuser
```

---

## Quick Test Commands

### Test MySQL Connection

```bash
# Test with credentials
mysql -u django_user -p gram_panchayat_db -e "SELECT 1;"

# Expected output:
# | 1 |
# | 1 |
```

### Test Django Connection

```bash
# In Django shell
python manage.py shell
>>> from django.db import connection
>>> print(connection.get_connection_params())
# Shows all connection parameters

>>> cursor = connection.cursor()
>>> cursor.execute("SELECT DATABASE();")
>>> print(cursor.fetchone())
# Should show database name

>>> exit()
```

### Test Models

```bash
python manage.py shell
>>> from portal_app.models import CustomUser
>>> CustomUser.objects.count()
# Should print a number (0 or more)

>>> CustomUser.objects.all()
# Should show list of users

>>> exit()
```

---

## Settings.py Quick Reference

### Minimal Configuration

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'gram_panchayat_db',
        'USER': 'django_user',
        'PASSWORD': 'django_password_123',
        'HOST': '127.0.0.1',
        'PORT': 3306,
    }
}
```

### Production Configuration

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'gram_panchayat_db',
        'USER': 'django_user',
        'PASSWORD': 'django_password_123',
        'HOST': '127.0.0.1',
        'PORT': 3306,
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
        'CONN_MAX_AGE': 600,
        'ATOMIC_REQUESTS': True,  # Better transaction handling
    }
}
```

---

## Common Commands for Debugging

```bash
# Show Django version
python -m django --version

# Check project
python manage.py check

# Check database connection
python manage.py shell -c "from django.db import connection; print(connection.get_connection_params())"

# List all models
python manage.py shell -c "from django.apps import apps; [print(m) for m in apps.get_models()]"

# Count users
python manage.py shell -c "from django.contrib.auth import get_user_model; print(get_user_model().objects.count())"

# Backup database
mysqldump -u django_user -p gram_panchayat_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Show MySQL variables
mysql -u root -p -e "SHOW VARIABLES LIKE 'max_connections';"
```

---

## Performance Tips

### Optimize Connection Pool

```python
DATABASES = {
    'default': {
        # ... other settings
        'CONN_MAX_AGE': 600,  # Reuse connections
        'CONN_HEALTH_CHECKS': True,  # Check connections before use (Django 4.1+)
    }
}
```

### Enable Query Logging (Development Only)

```python
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Optimize Queries

```python
# Use select_related for foreign keys
User.objects.select_related('profile').all()

# Use prefetch_related for reverse foreign keys
User.objects.prefetch_related('posts').all()

# Use only() to fetch specific fields
User.objects.only('id', 'username').all()

# Use values() to get dictionaries
User.objects.values('id', 'username')
```

---

## When to Reset Database

**Never do this in production!**

Use only when:
- Learning/development
- Testing migrations
- Major schema changes
- Starting fresh

```bash
# Reset (deletes all data)
python manage.py flush --no-input
python manage.py migrate
python manage.py createsuperuser
```

---

## Summary

✅ MySQL installed and running  
✅ Database and user created  
✅ Django settings configured  
✅ mysqlclient or mysql-connector-python installed  
✅ Migrations applied  
✅ Superuser created  
✅ Connection working  

**You're connected!** 🎉


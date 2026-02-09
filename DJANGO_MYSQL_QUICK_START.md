# ⚡ Django + MySQL Quick Start (5 Minutes)

## Step 1: Ensure MySQL is Running (30 seconds)

```powershell
Get-Service MySQL80
# Status: Running? YES ✓
```

---

## Step 2: Create Database & User (1 minute)

```sql
mysql -u root -p
# Enter root password

CREATE DATABASE gram_panchayat_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'django_user'@'localhost' IDENTIFIED BY 'django_password_123';
GRANT ALL PRIVILEGES ON gram_panchayat_db.* TO 'django_user'@'localhost';
FLUSH PRIVILEGES;

EXIT;
```

---

## Step 3: Install MySQL Library (1 minute)

```bash
# Activate virtual environment
cd d:\portal
.\venv\Scripts\Activate.ps1

# Install library
pip install mysqlclient==2.2.1

# If that fails, try:
pip install mysql-connector-python
```

---

## Step 4: Configure Django (1 minute)

**Edit: `gram_panchayat/settings.py`**

Replace DATABASES section with:

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
    }
}
```

---

## Step 5: Test Connection (1 minute)

```bash
# Run migrations
python manage.py migrate

# Expected: "Applying..." messages and "OK"
```

---

## Step 6: Create Admin User (1 minute)

```bash
python manage.py createsuperuser
# Enter username, email, password
```

---

## Done! Run Server

```bash
python manage.py runserver
```

Visit: **http://localhost:8000/admin/**

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| "No module named MySQLdb" | `pip install mysqlclient` |
| "Access denied" | Check username/password in settings |
| "Unknown database" | Run Step 2 again |
| "Can't connect" | Verify MySQL running: `Get-Service MySQL80` |

---

## Files Modified

✅ `gram_panchayat/settings.py` - DATABASES section

---

## Verification Checklist

```
✓ MySQL running
✓ Database created
✓ User created
✓ mysqlclient installed
✓ settings.py updated
✓ Migrations applied
✓ Superuser created
✓ Server running
✓ Admin accessible
```

**You're connected to MySQL!** 🎉

For detailed info, see: `DJANGO_MYSQL_CONNECTION.md`


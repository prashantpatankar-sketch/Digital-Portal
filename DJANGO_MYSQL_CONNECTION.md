# 🗄️ Django + MySQL Connection Guide

## Part 1: MySQL Installation & Database Setup

### Step 1a: Verify MySQL is Running

```powershell
# Check MySQL status
mysql --version

# Expected: mysql Ver 8.0.x for Windows on x86_64
```

If MySQL is not installed, see [SETUP_GUIDE.md](SETUP_GUIDE.md) Step 4-6.

### Step 1b: Create MySQL Database

```bash
# Login to MySQL
mysql -u root -p
# Enter your MySQL root password

# Create database for Django
CREATE DATABASE gram_panchayat_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Create user for Django (recommended)
CREATE USER 'django_user'@'localhost' IDENTIFIED BY 'django_secure_password_123';

# Grant privileges
GRANT ALL PRIVILEGES ON gram_panchayat_db.* TO 'django_user'@'localhost';

# Apply changes
FLUSH PRIVILEGES;

# Verify
SHOW DATABASES;
SELECT User FROM mysql.user WHERE Host='localhost';

# Exit MySQL
EXIT;
```

### Step 1c: Verify Database Connection

```bash
# Login with Django user
mysql -u django_user -p gram_panchayat_db
# Enter password: django_secure_password_123

# You should see:
# mysql>

# Exit
EXIT;
```

**Credentials for Django:**
```
Database Name: gram_panchayat_db
Username: django_user
Password: django_secure_password_123
Host: 127.0.0.1 (or localhost)
Port: 3306
```

---

## Part 2: Django Settings Configuration

### Method 1: Direct Configuration (Development Only)

**Edit: `gram_panchayat/settings.py`**

Find this section:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

Replace with:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'gram_panchayat_db',
        'USER': 'django_user',
        'PASSWORD': 'django_secure_password_123',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
        'CONN_MAX_AGE': 600,
    }
}
```

**Parameters Explained:**
| Parameter | Value | Meaning |
|-----------|-------|---------|
| ENGINE | django.db.backends.mysql | Use MySQL backend |
| NAME | gram_panchayat_db | Database name |
| USER | django_user | MySQL username |
| PASSWORD | django_secure_password_123 | MySQL password |
| HOST | 127.0.0.1 | Database server address |
| PORT | 3306 | MySQL port (default) |
| init_command | SET sql_mode=... | Ensure compatibility |
| charset | utf8mb4 | Unicode support |
| CONN_MAX_AGE | 600 | Connection pool timeout |

### Method 2: Environment Variables (Recommended for Production)

**Create: `.env` file in project root**

```
DEBUG=True
SECRET_KEY=your-secret-key-here
DB_ENGINE=django.db.backends.mysql
DB_NAME=gram_panchayat_db
DB_USER=django_user
DB_PASSWORD=django_secure_password_123
DB_HOST=127.0.0.1
DB_PORT=3306
```

**Add to `.gitignore`:**
```
.env
*.sqlite3
```

**Edit: `gram_panchayat/settings.py`**

Add at the top:
```python
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration from environment
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.mysql'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
        'CONN_MAX_AGE': 600,
    }
}
```

**Why this is better:**
- ✅ Secrets not in git
- ✅ Different config per environment
- ✅ Easy to change without code
- ✅ Production-ready

---

## Part 3: MySQL Connector Options

### Option A: mysqlclient (Recommended)

**Pros:**
- ✅ Official Python MySQL interface
- ✅ Fastest performance
- ✅ Full feature support
- ✅ Used by Django officially

**Cons:**
- ❌ Requires C compiler (Visual C++ Build Tools)
- ❌ Slower installation

**Installation:**

```bash
# Install Visual C++ Build Tools first (if needed)
# Download from: https://visualstudio.microsoft.com/downloads/
# Select: "Desktop Development with C++"

# Install mysqlclient
pip install mysqlclient==2.2.1
```

**Verify:**
```bash
python -c "import MySQLdb; print('✓ mysqlclient installed')"
```

**In Django settings:**
```python
'ENGINE': 'django.db.backends.mysql'
```

---

### Option B: mysql-connector-python

**Pros:**
- ✅ Official MySQL connector
- ✅ No C compiler needed
- ✅ Easy installation
- ✅ Cross-platform

**Cons:**
- ❌ Slower than mysqlclient
- ❌ Less feature complete

**Installation:**

```bash
pip install mysql-connector-python
```

**Verify:**
```bash
python -c "import mysql.connector; print('✓ mysql-connector-python installed')"
```

**In Django settings:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'gram_panchayat_db',
        'USER': 'django_user',
        'PASSWORD': 'django_secure_password_123',
        'HOST': '127.0.0.1',
        'PORT': 3306,
    }
}
```

---

### Option C: PyMySQL

**Pros:**
- ✅ Pure Python (no C compiler)
- ✅ Easy installation
- ✅ Good documentation

**Cons:**
- ❌ Slower performance
- ❌ Limited features

**Installation:**

```bash
pip install PyMySQL
```

**Enable in Django (settings.py):**
```python
# Add at the very top of settings.py
import pymysql
pymysql.install_as_MySQLdb()
```

---

## Comparison Table

| Feature | mysqlclient | mysql-connector-python | PyMySQL |
|---------|-------------|------------------------|---------|
| Installation | Requires C compiler | Simple | Simple |
| Performance | Fastest | Medium | Slowest |
| Django Official Support | Yes | Yes | Yes |
| Features | Complete | Good | Limited |
| Production Ready | Yes | Yes | Yes |
| Maintenance | Active | Active | Active |
| Recommended | ✅ YES | ✅ Good | ✓ OK |

**Recommendation:** Use `mysqlclient` for production, `mysql-connector-python` if you can't install C compiler.

---

## Part 4: Connect to Your Django Project

### Step 1: Ensure MySQL is Running

```bash
# Check MySQL service (Windows)
Get-Service MySQL80
# Status should be: Running

# If not running:
Start-Service MySQL80
```

### Step 2: Test Database Connection

```bash
# From your Django project directory
cd d:\portal

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Test connection
python manage.py shell
```

```python
# In Django shell:
>>> from django.db import connection
>>> print(connection.connection)
# Should print connection details (not None)

>>> cursor = connection.cursor()
>>> cursor.execute("SELECT 1")
>>> print(cursor.fetchone())
# Should print: (1,)

>>> exit()
```

### Step 3: Run Migrations

```bash
# Create migrations for built-in apps
python manage.py migrate
```

**Expected output:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying auth.0002_alter_user_...  OK
  ... (more migrations)
```

### Step 4: Create Superuser

```bash
python manage.py createsuperuser
# Enter username, email, password
```

### Step 5: Run Development Server

```bash
python manage.py runserver
```

Visit: `http://localhost:8000/admin/`

---

## Part 5: Common Connection Errors & Fixes

### Error 1: "No module named 'MySQLdb'"

**Cause:** mysqlclient not installed

**Fix:**
```bash
pip install mysqlclient==2.2.1
```

**If installation fails:**
```bash
# Install Visual C++ Build Tools first
# Then retry pip install

# Or use mysql-connector-python instead:
pip install mysql-connector-python
```

---

### Error 2: "ModuleNotFoundError: No module named 'mysql'"

**Cause:** Neither MySQL library installed

**Fix:**
```bash
# Option A (Recommended):
pip install mysqlclient==2.2.1

# Option B (If A fails):
pip install mysql-connector-python
```

---

### Error 3: "Access denied for user 'django_user'@'localhost'"

**Cause:** Wrong password or user doesn't exist

**Fix:**
```bash
# Verify user and password
mysql -u root -p gram_panchayat_db
# Enter root password

# Check users
SELECT User, Host FROM mysql.user;

# If django_user missing, create it:
CREATE USER 'django_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON gram_panchayat_db.* TO 'django_user'@'localhost';
FLUSH PRIVILEGES;

# Exit
EXIT;
```

**Update Django settings:**
```python
'USER': 'django_user',
'PASSWORD': 'your_password',  # Must match!
```

---

### Error 4: "Can't connect to MySQL server on '127.0.0.1' (10061)"

**Cause:** MySQL server not running

**Fix:**
```bash
# Check if running
Get-Service MySQL80

# Start service
Start-Service MySQL80

# Or start manually:
# 1. Open Services (services.msc)
# 2. Find MySQL80
# 3. Right-click → Start
```

---

### Error 5: "No database 'gram_panchayat_db'"

**Cause:** Database not created in MySQL

**Fix:**
```bash
# Login to MySQL
mysql -u root -p

# Create database
CREATE DATABASE gram_panchayat_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Verify
SHOW DATABASES;

# Exit
EXIT;
```

**Update Django settings:** Ensure NAME matches exactly.

---

### Error 6: "1045: Access denied for user 'root'@'localhost' (using password: YES)"

**Cause:** Wrong MySQL root password

**Fix:**
```bash
# Test with correct password
mysql -u root -p
# Enter your MySQL root password correctly

# If you forgot the password:
# 1. Stop MySQL80 service
# 2. Start MySQL without grant tables:
#    mysqld --skip-grant-tables
# 3. Reset password:
#    mysql -u root
#    FLUSH PRIVILEGES;
#    ALTER USER 'root'@'localhost' IDENTIFIED BY 'newpassword';
```

---

### Error 7: "Incompatible Python version"

**Cause:** mysqlclient doesn't support your Python version

**Fix:**
```bash
# Check Python version
python --version

# If Python 3.13+, use mysql-connector-python:
pip uninstall mysqlclient
pip install mysql-connector-python
```

---

### Error 8: "django.db.utils.OperationalError: Can't initialize database"

**Cause:** Database connection issue

**Fix:**
```bash
# 1. Verify MySQL is running
Get-Service MySQL80

# 2. Test connection manually
mysql -u django_user -p gram_panchayat_db

# 3. Check Django settings.py
# HOST should be '127.0.0.1' or 'localhost'
# PORT should be '3306'
# NAME, USER, PASSWORD must match

# 4. Check .env file (if using decouple)
# All values must be correct

# 5. Run migrations again
python manage.py migrate
```

---

### Error 9: "You must use the 'encoding' option or 'charset' option"

**Cause:** Missing charset configuration

**Fix:**
```python
# In settings.py DATABASES:
'OPTIONS': {
    'charset': 'utf8mb4',
    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
}
```

---

### Error 10: "Lost connection to MySQL server"

**Cause:** Network timeout or MySQL crashed

**Fix:**
```python
# In settings.py DATABASES:
'CONN_MAX_AGE': 600,  # Add this (10 min timeout)
'OPTIONS': {
    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    'charset': 'utf8mb4',
}
```

**Also restart MySQL:**
```bash
Restart-Service MySQL80
```

---

### Error 11: "1055 GROUP BY clause error"

**Cause:** sql_mode not set correctly

**Fix:**
```python
# In settings.py DATABASES:
'OPTIONS': {
    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    'charset': 'utf8mb4',
}
```

Run migrations again:
```bash
python manage.py migrate
```

---

### Error 12: "ERROR 2002 (HY000): Can't connect to local MySQL server"

**Cause:** MySQL socket or pipe issue on Windows

**Fix:**
```python
# In settings.py, use explicit host:
'HOST': '127.0.0.1',  # Not 'localhost'
'PORT': 3306,         # Explicit port
```

---

## Part 6: Verification Checklist

### Before Running Django

```bash
# 1. MySQL running?
Get-Service MySQL80
# Status: Running ✓

# 2. Database exists?
mysql -u root -p
> SHOW DATABASES;
# gram_panchayat_db exists ✓
> EXIT;

# 3. User exists and has access?
mysql -u django_user -p gram_panchayat_db
# Successful login ✓
> EXIT;

# 4. Django library installed?
pip list | grep -i mysql
# mysqlclient or mysql-connector-python listed ✓

# 5. Virtual environment activated?
# Prompt shows (venv) prefix ✓
```

### In Django Project

```bash
# 6. Run migrations
python manage.py migrate
# All OK messages ✓

# 7. Test shell connection
python manage.py shell
>>> from django.db import connection
>>> connection.ensure_connection()
>>> exit()
# No errors ✓

# 8. Create superuser
python manage.py createsuperuser
# Successful ✓

# 9. Run server
python manage.py runserver
# Starting development server at http://127.0.0.1:8000/ ✓

# 10. Visit admin
# http://localhost:8000/admin/
# Login works ✓
```

---

## Part 7: Complete settings.py Example

```python
"""
Django settings for gram_panchayat project.
"""

from pathlib import Path
from decouple import config
import os

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'portal_app',  # Your app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gram_panchayat.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gram_panchayat.wsgi.application'

# ════════════════════════════════════════════════════════════
# DATABASE - MYSQL CONFIGURATION
# ════════════════════════════════════════════════════════════

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='gram_panchayat_db'),
        'USER': config('DB_USER', default='django_user'),
        'PASSWORD': config('DB_PASSWORD', default='django_secure_password_123'),
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default=3306, cast=int),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
        'CONN_MAX_AGE': 600,
    }
}

# ════════════════════════════════════════════════════════════
# PASSWORD VALIDATION
# ════════════════════════════════════════════════════════════

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ════════════════════════════════════════════════════════════
# INTERNATIONALIZATION
# ════════════════════════════════════════════════════════════

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ════════════════════════════════════════════════════════════
# STATIC FILES
# ════════════════════════════════════════════════════════════

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# ════════════════════════════════════════════════════════════
# MEDIA FILES
# ════════════════════════════════════════════════════════════

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ════════════════════════════════════════════════════════════
# AUTHENTICATION
# ════════════════════════════════════════════════════════════

AUTH_USER_MODEL = 'portal_app.CustomUser'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'

# ════════════════════════════════════════════════════════════
# DEFAULT PRIMARY KEY FIELD TYPE
# ════════════════════════════════════════════════════════════

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

---

## Part 8: Migration & Database Management

### First Time Setup

```bash
# 1. Create migrations for all apps
python manage.py makemigrations

# 2. Apply migrations to MySQL
python manage.py migrate

# 3. Check migration status
python manage.py migrate --list

# 4. Create superuser
python manage.py createsuperuser
```

### Backup Your MySQL Database

```bash
# Backup
mysqldump -u django_user -p gram_panchayat_db > backup.sql
# Enter password when prompted

# Restore from backup
mysql -u django_user -p gram_panchayat_db < backup.sql
```

### Reset Database

```bash
# ⚠️ WARNING: This deletes all data!

# 1. Flush all data
python manage.py flush

# 2. Re-run migrations
python manage.py migrate

# 3. Create new superuser
python manage.py createsuperuser
```

---

## Summary Checklist

```
✓ MySQL installed and running
✓ Database created (gram_panchayat_db)
✓ User created (django_user)
✓ MySQL library installed (mysqlclient or mysql-connector-python)
✓ settings.py configured with MySQL
✓ Migrations applied (python manage.py migrate)
✓ Superuser created
✓ Django connected to MySQL successfully
✓ Admin interface works at /admin/
✓ Database backups created
```

You're now ready to use Django with MySQL! 🎉


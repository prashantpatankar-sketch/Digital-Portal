# 🔧 Django Project Management Commands Reference

## Creating Projects & Apps

### Create a New Project
```bash
django-admin startproject myproject
# Creates:
# myproject/
# ├── manage.py
# └── myproject/
#     ├── __init__.py
#     ├── settings.py
#     ├── urls.py
#     ├── asgi.py
#     └── wsgi.py
```

### Create a New App (inside project)
```bash
cd myproject
python manage.py startapp myapp
# Creates:
# myapp/
# ├── migrations/
# ├── __init__.py
# ├── admin.py
# ├── apps.py
# ├── models.py
# ├── tests.py
# ├── views.py
# └── urls.py
```

### Create Multiple Apps
```bash
python manage.py startapp certificates
python manage.py startapp complaints
python manage.py startapp payments
# Then register in settings.py INSTALLED_APPS
```

---

## Development Server

### Basic Server Start
```bash
python manage.py runserver
# Runs on http://127.0.0.1:8000/
```

### Run on Specific Port
```bash
python manage.py runserver 8001
python manage.py runserver 9000
```

### Run on All Network Interfaces
```bash
python manage.py runserver 0.0.0.0:8000
# Now accessible from other computers on network
# http://your_computer_ip:8000/
```

### Run with Auto-reload
```bash
python manage.py runserver --reload
# Default behavior - automatically restarts when you change code
```

### Run in Production Mode (no debug)
```bash
python manage.py runserver --settings=myproject.settings_production
```

---

## Database Commands

### Make Migrations (Create change files)
```bash
# All apps
python manage.py makemigrations

# Specific app
python manage.py makemigrations certificates

# Show what migrations will be created (dry-run)
python manage.py makemigrations --dry-run

# Show the generated SQL
python manage.py makemigrations --dry-run --verbosity 2
```

### Apply Migrations (Execute changes)
```bash
# Apply all pending migrations
python manage.py migrate

# Apply migrations for specific app
python manage.py migrate certificates

# Migrate to specific migration
python manage.py migrate certificates 0003

# Rollback to previous migration
python manage.py migrate certificates 0001

# Show migration status
python manage.py migrate --list
```

### Show Migration SQL Without Running
```bash
python manage.py sqlmigrate certificates 0001
# Shows the SQL that will be executed
```

### Create Empty Migration (for custom SQL)
```bash
python manage.py makemigrations --empty certificates --name add_custom_sql
# Creates: certificates/migrations/0002_add_custom_sql.py
```

### Reset Database
```bash
# Delete all data but keep tables
python manage.py flush

# Flush with confirmation
python manage.py flush --no-input

# Drop everything and recreate
python manage.py migrate zero certificates
python manage.py migrate certificates
```

### Squash Migrations (Combine multiple migrations)
```bash
# Combine first 5 migrations into 1
python manage.py squashmigrations certificates 0005
# Reduces migration file bloat for large projects
```

---

## Admin User Management

### Create Superuser (Admin Account)
```bash
python manage.py createsuperuser
# Interactive prompt:
# Username: admin
# Email: admin@example.com
# Password: ****
```

### Create Superuser Non-Interactively
```bash
python manage.py createsuperuser --noinput --username=admin --email=admin@example.com
# Then set password manually:
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> u = User.objects.get(username='admin')
>>> u.set_password('newpassword')
>>> u.save()
```

### Change Password
```bash
python manage.py changepassword admin
# Interactive prompt for new password
```

### Create Regular User Programmatically
```bash
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.create_user(username='john', password='pass123')
>>> user.save()
```

---

## Interactive Shell

### Open Django Shell
```bash
python manage.py shell
# Interactive Python with Django context loaded
```

### Run Commands in Shell
```bash
python manage.py shell
>>> from myapp.models import User
>>> users = User.objects.all()
>>> print(users)
>>> user = User.objects.create(username='john')
>>> user.save()
>>> exit()
```

### Direct Shell Command
```bash
python manage.py shell -c "from myapp.models import User; print(User.objects.count())"
```

### IPython Shell (if installed)
```bash
pip install ipython
python manage.py shell
# Now uses IPython for better features (autocomplete, syntax highlighting)
```

---

## Testing

### Run All Tests
```bash
python manage.py test
# Runs all test_*.py files in all apps
```

### Run Tests for Specific App
```bash
python manage.py test certificates
```

### Run Specific Test Class
```bash
python manage.py test certificates.tests.CertificateCreationTest
```

### Run Specific Test Method
```bash
python manage.py test certificates.tests.CertificateCreationTest.test_valid_certificate
```

### Run Tests with Verbosity
```bash
python manage.py test --verbosity=2
# 0 = no output
# 1 = minimal output (default)
# 2 = normal output
# 3 = maximum output
```

### Keep Test Database (for debugging)
```bash
python manage.py test --keepdb
# Reuses test database from previous run (faster)
```

### Run Tests with Coverage
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Creates htmlcov/index.html
```

---

## Static Files

### Collect Static Files (for production)
```bash
python manage.py collectstatic
# Gathers CSS, JS, images into STATIC_ROOT directory
```

### Collect Without Prompt
```bash
python manage.py collectstatic --noinput
```

### Clear Old Static Files First
```bash
python manage.py collectstatic --clear
# Removes old files before collecting new ones
```

### Dry Run (See what would be collected)
```bash
python manage.py collectstatic --dry-run --verbosity=2
```

### Find Static Files
```bash
python manage.py findstatic css/style.css
# Shows where style.css would be found
```

---

## Data Management

### Export Data (Dump)
```bash
# Export all data
python manage.py dumpdata > backup.json

# Export specific app
python manage.py dumpdata certificates > certificates.json

# Export specific model
python manage.py dumpdata certificates.Certificate > certificates_only.json

# Pretty format (indented)
python manage.py dumpdata --indent=2 > backup.json

# YAML format
python manage.py dumpdata --format=yaml > backup.yaml
```

### Import Data (Load)
```bash
# Load all data
python manage.py loaddata backup.json

# Load specific fixture
python manage.py loaddata certificates.json

# Clear before loading
python manage.py flush --no-input
python manage.py loaddata backup.json
```

### Clear All Data
```bash
python manage.py flush
# Prompts for confirmation

python manage.py flush --no-input
# No confirmation
```

---

## Debugging & Inspection

### Check Django Installation
```bash
python -m django --version
# Shows Django version
```

### Check Project Status
```bash
python manage.py check
# Checks for configuration errors

python manage.py check --deploy
# Checks for production-ready issues
```

### Show All Available Commands
```bash
python manage.py help
# Lists all available commands

python manage.py help makemigrations
# Shows help for specific command
```

### Show SQL Queries
```bash
python manage.py shell
>>> from django.db import connection
>>> from django.test.utils import CaptureQueriesContext
>>> with CaptureQueriesContext(connection) as context:
...     User.objects.all()
>>> for query in context:
...     print(query['sql'])
```

### List All Models
```bash
python manage.py shell
>>> from django.apps import apps
>>> for model in apps.get_models():
...     print(model)
```

### Inspect Database Schema
```bash
python manage.py sqlall certificates
# Shows CREATE TABLE statements for app

python manage.py sqlall
# Shows for all apps
```

---

## Sessions & Cache

### Clear Sessions
```bash
python manage.py clearsessions
# Removes expired session files/database entries
```

### Clear Cache
```bash
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

---

## Debugging & Logging

### Run with Verbose Output
```bash
python manage.py migrate --verbosity=2
python manage.py runserver --verbosity=2
```

### Enable Query Logging
```bash
# In settings.py
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

---

## Production Deployment

### Collect Static Files
```bash
python manage.py collectstatic --noinput --clear
```

### Check Deployment Readiness
```bash
python manage.py check --deploy
```

### Create a Comprehensive Backup
```bash
# Database
mysqldump -u user -p database_name > backup.sql

# Media files
tar -czf media_backup.tar.gz media/

# Both
tar -czf project_backup.tar.gz . --exclude=venv --exclude=.git
```

### Run With Gunicorn (Production Server)
```bash
pip install gunicorn
gunicorn myproject.wsgi:application --bind 0.0.0.0:8000
```

### Run With Multiple Workers
```bash
gunicorn myproject.wsgi:application --workers 4 --bind 0.0.0.0:8000
```

---

## Environment Management

### Create requirements.txt
```bash
pip freeze > requirements.txt
```

### Install from requirements.txt
```bash
pip install -r requirements.txt
```

### Show Installed Packages
```bash
pip list
pip show Django
```

---

## Common Workflow

```bash
# 1. Create project
django-admin startproject myproject
cd myproject

# 2. Create app
python manage.py startapp myapp

# 3. Define models in myapp/models.py
# (Edit the file manually)

# 4. Create migration
python manage.py makemigrations

# 5. Apply migration
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Register models in admin.py
# admin.site.register(MyModel)

# 8. Run server
python manage.py runserver

# 9. Visit http://localhost:8000/admin/
```

---

## Useful Shortcuts

### Run Command in One Line (No Interactive Shell)
```bash
python manage.py shell -c "from myapp.models import User; print(User.objects.count())"
```

### Alias for Frequently Used Commands (Linux/Mac)
```bash
# Add to ~/.bashrc or ~/.zshrc
alias djrun="python manage.py runserver"
alias djtest="python manage.py test"
alias djmigrate="python manage.py migrate"
alias djmake="python manage.py makemigrations"

# Then use:
djrun
djtest
```

### Run Tests in Parallel
```bash
python manage.py test --parallel auto
# Uses all CPU cores for faster testing
```


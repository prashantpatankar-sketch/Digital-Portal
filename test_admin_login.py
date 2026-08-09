#!/usr/bin/env python
"""
Test Admin Login Process
"""
import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('d:/portal')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gram_panchayat.settings')
import django
django.setup()

from django.conf import settings
from django.test import Client
from portal_app.models import CustomUser

# The Django test client defaults to host "testserver".
# Ensure the host is allowed when running this standalone script.
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ['testserver']

def test_admin_login():
    print("=== Testing Admin Login ===")
    
    # Check admin user
    try:
        admin = CustomUser.objects.get(username='admin')
        print(f"✅ Admin user found: {admin.username}")
        print(f"✅ Admin role: {admin.role}")
        print(f"✅ Admin active: {admin.is_active}")
        print(f"✅ Admin email: {admin.email}")
        
        # Test password
        password_correct = admin.check_password('admin123')
        print(f"✅ Password correct: {password_correct}")
        
    except CustomUser.DoesNotExist:
        print("❌ Admin user not found!")
        return False
    
    # Test login process
    print("\n=== Testing Login Process ===")
    client = Client()
    
    # Get login page
    response = client.get('/admin_login/')
    print(f"✅ Login page status: {response.status_code}")
    
    # Test login
    login_data = {
        'username': 'admin',
        'password': 'admin123',
        'csrfmiddlewaretoken': 'test'
    }
    
    # Get CSRF token first
    response = client.get('/admin_login/')
    csrf_token = None
    if 'csrftoken' in client.cookies:
        csrf_token = client.cookies['csrftoken'].value
    
    if csrf_token:
        login_data['csrfmiddlewaretoken'] = csrf_token
        print(f"✅ CSRF token: {csrf_token[:20]}...")
    
    # Test login POST
    response = client.post('/admin_login/', data=login_data)
    print(f"✅ Login POST status: {response.status_code}")
    
    if response.status_code == 302:
        print("✅ Login successful - redirecting")
        print(f"✅ Redirect location: {response.get('Location', 'No location')}")
        
        # Follow redirect
        response = client.get(response.get('Location'))
        print(f"✅ Dashboard status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Dashboard loaded successfully!")
            return True
        else:
            print(f"❌ Dashboard error: {response.content[:200]}")
            return False
    else:
        print(f"❌ Login failed: {response.content[:200]}")
        return False

if __name__ == '__main__':
    test_admin_login()

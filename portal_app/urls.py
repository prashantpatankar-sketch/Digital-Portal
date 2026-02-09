"""
URL Configuration for Portal App
"""

from django.urls import path
from . import views

urlpatterns = [
    # Public URLs
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('track/', views.track_application, name='track_application'),
    
    # Authentication URLs
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # OTP Email Verification URLs
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    
    # Citizen Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Certificate Applications
    path('apply/birth-certificate/', views.apply_birth_certificate, name='apply_birth_certificate'),
    path('apply/death-certificate/', views.apply_death_certificate, name='apply_death_certificate'),
    path('apply/income-certificate/', views.apply_income_certificate, name='apply_income_certificate'),
    
    # Tax Payment
    path('pay-tax/', views.pay_tax, name='pay_tax'),
    
    # Complaints
    path('file-complaint/', views.file_complaint, name='file_complaint'),
    path('my-complaints/', views.my_complaints, name='my_complaints'),
    path('complaint/<int:complaint_id>/', views.complaint_detail, name='complaint_detail'),
    
    # Application Management
    path('my-applications/', views.my_applications, name='my_applications'),
    path('application/<int:application_id>/', views.application_detail, name='application_detail'),
    path('download-certificate/<int:application_id>/', views.download_certificate, name='download_certificate'),
    
    # Admin URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/applications/', views.admin_applications, name='admin_applications'),
    path('admin/application/<int:application_id>/review/', views.admin_review_application, name='admin_review_application'),
    path('admin/complaints/', views.admin_complaints, name='admin_complaints'),
    path('admin/complaint/<int:complaint_id>/update/', views.admin_update_complaint, name='admin_update_complaint'),
]

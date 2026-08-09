"""
URL Configuration for Portal App
"""

from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Public URLs
    path('', RedirectView.as_view(pattern_name='home', permanent=False)),
    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('track/', views.track_application, name='track_application'),
    path('access-denied/', views.access_denied, name='access_denied'),
    path('email-preview/', views.email_template_preview, name='email_template_preview'),
    
    # Authentication URLs
    path('register/', views.register_view, name='register'),
    path('register-multi-step/', views.register_multi_step_view, name='register_multi_step'),
    path('register/verify-otp/', views.register_verify_otp_view, name='register_verify_otp'),
    path('register/resend-otp/', views.register_resend_otp_view, name='register_resend_otp'),
    path('login/', views.login_view, name='login'),
    path('admin_login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.logout_view, name='logout'),
    path('settings/', views.account_settings, name='settings'),
    path('account/settings/', views.account_settings, name='account_settings'),
    path('account/delete/', views.delete_account, name='delete_account'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('forgot-password/verify-otp/', views.forgot_password_verify_otp_view, name='forgot_password_verify_otp'),
    path('forgot-password/resend-otp/', views.forgot_password_resend_otp_view, name='forgot_password_resend_otp'),
    path('forgot-password/set-new-password/', views.forgot_password_set_new_password_view, name='forgot_password_set_new_password'),
    
    # OTP Email Verification URLs
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    
    # Citizen Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('activity-history/', views.activity_history, name='activity_history'),
    path('payments/', views.payments, name='payments'),
    path('payments/pay-bills/', views.pay_bills, name='pay_bills'),
    path('payments/history/', views.payment_history, name='payment_history'),
    path('download-center/', views.download_center, name='download_center'),
    path('profile/', views.profile, name='profile'),
    path('account/profile/', views.profile, name='account_profile'),
    path('notifications/', views.notifications_center, name='notifications'),
    path('notifications-center/', views.notifications_center, name='notifications_center'),

    # Smart UX APIs
    path('api/search/', views.smart_search_api, name='smart_search_api'),
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
    path('api/dashboard/data/', views.dashboard_data_api, name='dashboard_data_api'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('api/notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # Certificate Applications
    path('apply/birth-certificate/', views.apply_birth_certificate, name='apply_birth_certificate'),
    path('apply/death-certificate/', views.apply_death_certificate, name='apply_death_certificate'),
    path('apply/income-certificate/', views.apply_income_certificate, name='apply_income_certificate'),
    
    # Tax Payment
    path('pay-tax/', views.pay_tax, name='pay_tax'),
    path('services/electricity-bill/', views.electricity_bill_service, name='electricity_bill_service'),
    path('services/water-bill/', views.water_bill_service, name='water_bill_service'),
    path('services/property-tax/', views.property_tax_service, name='property_tax_service'),
    path('services/bill-request/', views.submit_bill_request, name='submit_bill_request'),
    path('services/bill-pdf/<str:service_type>/<int:record_id>/', views.download_service_bill_pdf, name='download_service_bill_pdf'),
    
    # Complaints
    path('file-complaint/', views.file_complaint, name='file_complaint'),
    path('my-complaints/', views.my_complaints, name='my_complaints'),
    path('complaint/<int:complaint_id>/', views.complaint_detail, name='complaint_detail'),
    
    # Application Management
    path('my-applications/', views.my_applications, name='my_applications'),
    path('my-certificates/', views.my_certificates, name='my_certificates'),
    path('application/<int:application_id>/', views.application_detail, name='application_detail'),
    path('download-certificate/<int:application_id>/', views.download_certificate, name='download_certificate'),
    
    # Admin URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('system-admin-panel/', views.system_admin_panel, name='system_admin_panel'),
    path('panel/staff/create/', views.create_staff, name='create_staff'),
    path('panel/staff/create-admin/', views.create_staff, name='admin_create_staff'),
    path('panel/staff/', views.staff_management, name='staff_management'),
    path('panel/staff/<int:user_id>/edit/', views.admin_edit_staff, name='admin_edit_staff'),
    path('panel/staff/<int:user_id>/toggle/', views.admin_toggle_staff_status, name='admin_toggle_staff_status'),
    path('panel/staff/<int:user_id>/delete/', views.admin_delete_staff, name='admin_delete_staff'),
    path('panel/applications/<int:application_id>/action/', views.staff_application_action, name='staff_application_action'),
    path('panel/users/', views.admin_users, name='admin_users'),
    path('panel/users/<int:user_id>/edit/', views.admin_edit_user, name='admin_edit_user'),
    path('panel/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('panel/applications/', views.admin_applications, name='admin_applications'),
    path('panel/application/<int:application_id>/review/', views.admin_review_application, name='admin_review_application'),
    path('panel/applications/delete/<int:id>/', views.delete_application, name='delete_application'),
    path('panel/applications/export/', views.export_applications, name='export_applications'),
    path('panel/complaints/', views.admin_complaints, name='admin_complaints'),
    path('panel/complaint/<int:complaint_id>/update/', views.admin_update_complaint, name='admin_update_complaint'),
    path('panel/reports/', views.admin_reports, name='admin_reports'),
    path('panel/reports/send/', views.trigger_admin_report, name='trigger_admin_report'),
    path('panel/api/stats/', views.admin_stats_api, name='admin_stats_api'),
    path('panel/api/stats/live/', views.admin_stats_api, name='admin_stats_live_api'),
]

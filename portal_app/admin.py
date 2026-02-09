"""
Admin Configuration for Portal App
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Application, BirthCertificate, DeathCertificate,
    IncomeCertificate, TaxPayment, Complaint, ApplicationStatusHistory,
    ComplaintHistory, EmailOTP
)


# ============================================
# CUSTOM USER ADMIN
# ============================================

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Custom admin interface for CustomUser model
    """
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'phone_number', 'email_verified', 'is_active', 'created_at']
    list_filter = ['role', 'email_verified', 'is_active', 'is_staff', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'aadhar_number']
    ordering = ['-created_at']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': ('role', 'phone_number', 'aadhar_number', 'date_of_birth', 'profile_photo', 'is_verified')
        }),
        ('Email Verification', {
            'fields': ('email_verified', 'email_verified_at')
        }),
        ('Address', {
            'fields': ('address', 'village', 'taluka', 'district', 'state', 'pincode')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': ('role', 'phone_number', 'email', 'first_name', 'last_name')
        }),
    )


# ============================================
# APPLICATION ADMIN
# ============================================

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """
    Admin interface for Application model
    """
    list_display = ['application_number', 'applicant', 'application_type', 'status', 'applied_date', 'reviewed_by']
    list_filter = ['status', 'application_type', 'applied_date']
    search_fields = ['application_number', 'applicant__username', 'applicant__email']
    readonly_fields = ['application_number', 'applied_date']
    ordering = ['-applied_date']
    
    fieldsets = (
        ('Application Details', {
            'fields': ('application_number', 'applicant', 'application_type', 'status')
        }),
        ('Tracking', {
            'fields': ('applied_date', 'reviewed_date', 'reviewed_by', 'admin_remarks')
        }),
    )


# ============================================
# CERTIFICATE ADMINS
# ============================================

@admin.register(BirthCertificate)
class BirthCertificateAdmin(admin.ModelAdmin):
    """
    Admin interface for Birth Certificate
    """
    list_display = ['child_name', 'date_of_birth', 'application', 'certificate_number', 'issued_date']
    list_filter = ['date_of_birth', 'issued_date']
    search_fields = ['child_name', 'father_name', 'mother_name', 'certificate_number']
    readonly_fields = ['application']
    ordering = ['-application__applied_date']


@admin.register(DeathCertificate)
class DeathCertificateAdmin(admin.ModelAdmin):
    """
    Admin interface for Death Certificate
    """
    list_display = ['deceased_name', 'date_of_death', 'deceased_age', 'application', 'certificate_number', 'issued_date']
    list_filter = ['date_of_death', 'issued_date']
    search_fields = ['deceased_name', 'informant_name', 'certificate_number']
    readonly_fields = ['application']
    ordering = ['-application__applied_date']


@admin.register(IncomeCertificate)
class IncomeCertificateAdmin(admin.ModelAdmin):
    """
    Admin interface for Income Certificate
    """
    list_display = ['applicant_name', 'annual_income', 'income_source', 'application', 'certificate_number', 'issued_date']
    list_filter = ['income_source', 'issued_date']
    search_fields = ['applicant_name', 'father_husband_name', 'certificate_number']
    readonly_fields = ['application']
    ordering = ['-application__applied_date']


# ============================================
# TAX PAYMENT ADMIN
# ============================================

@admin.register(TaxPayment)
class TaxPaymentAdmin(admin.ModelAdmin):
    """
    Admin interface for Tax Payment
    """
    list_display = ['property_number', 'tax_type', 'financial_year', 'tax_amount', 'payment_status', 'application']
    list_filter = ['tax_type', 'payment_status', 'financial_year']
    search_fields = ['property_number', 'transaction_id', 'receipt_number']
    readonly_fields = ['application', 'total_amount']
    ordering = ['-application__applied_date']


# ============================================
# COMPLAINT ADMIN
# ============================================

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    """
    Admin interface for Complaint
    """
    list_display = ['complaint_number', 'complainant', 'category', 'subject', 'priority', 'status', 'filed_date']
    list_filter = ['status', 'priority', 'category', 'filed_date']
    search_fields = ['complaint_number', 'subject', 'complainant__username']
    readonly_fields = ['complaint_number', 'filed_date']
    ordering = ['-filed_date']
    
    fieldsets = (
        ('Complaint Details', {
            'fields': ('complaint_number', 'complainant', 'category', 'subject', 'description', 'location')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'assigned_to')
        }),
        ('Tracking', {
            'fields': ('filed_date', 'resolved_date', 'resolution_remarks')
        }),
        ('Attachments', {
            'fields': ('complaint_photo',)
        }),
    )


# ============================================
# STATUS HISTORY ADMIN
# ============================================

@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Application Status History
    """
    list_display = ['application', 'old_status', 'new_status', 'changed_by', 'changed_at']
    list_filter = ['new_status', 'changed_at']
    search_fields = ['application__application_number']
    readonly_fields = ['changed_at']
    ordering = ['-changed_at']


@admin.register(ComplaintHistory)
class ComplaintHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Complaint History
    """
    list_display = ['complaint', 'action', 'old_value', 'new_value', 'performed_by', 'performed_at']
    list_filter = ['action', 'performed_at']
    search_fields = ['complaint__complaint_number', 'notes']
    readonly_fields = ['performed_at']
    ordering = ['-performed_at']


# ============================================
# OTP EMAIL VERIFICATION ADMIN
# ============================================

@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    """
    Admin interface for Email OTP Verification
    
    Security:
    - OTP code is displayed (admin only)
    - Read-only for most fields
    - Filterable by verification status
    """
    list_display = ['user', 'email', 'otp_code', 'is_verified', 'is_used', 'verification_attempts', 'created_at', 'expires_at', 'time_status']
    list_filter = ['is_verified', 'is_used', 'created_at', 'expires_at']
    search_fields = ['user__username', 'user__email', 'email', 'otp_code']
    readonly_fields = ['user', 'email', 'otp_code', 'created_at', 'expires_at', 'verified_at', 'verification_attempts', 'is_verified', 'is_used', 'time_status']
    ordering = ['-created_at']
    
    fieldsets = (
        ('OTP Information', {
            'fields': ('user', 'email', 'otp_code')
        }),
        ('Verification Status', {
            'fields': ('is_verified', 'is_used', 'verification_attempts', 'verified_at')
        }),
        ('Timing', {
            'fields': ('created_at', 'expires_at', 'time_status')
        }),
    )
    
    def time_status(self, obj):
        """Display whether OTP is expired or active"""
        from django.utils import timezone
        from django.utils.html import format_html
        
        if obj.is_verified:
            return format_html('<span style="color: green; font-weight: bold;">✓ Verified</span>')
        elif obj.is_used:
            return format_html('<span style="color: gray;">Used</span>')
        elif timezone.now() > obj.expires_at:
            return format_html('<span style="color: red; font-weight: bold;">⏰ Expired</span>')
        else:
            remaining = obj.get_time_remaining()
            minutes = remaining // 60
            seconds = remaining % 60
            return format_html(
                '<span style="color: orange; font-weight: bold;">⏳ Active ({}m {}s left)</span>',
                minutes, seconds
            )
    
    time_status.short_description = 'Status'
    
    def has_add_permission(self, request):
        """Prevent manual OTP creation"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make OTPs read-only"""
        return False


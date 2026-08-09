"""
Database Models for Digital Gram Panchayat Portal

This file contains all database models representing:
- Custom User Model (Citizens & Admins)
- Applications (Birth, Death, Income Certificates)
- Tax Payments (Water & House Tax)
- Complaints
- Application Status History
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import check_password, make_password
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone
from datetime import timedelta


# ============================================
# CUSTOM USER MODEL
# ============================================

class CustomUser(AbstractUser):
    """
    Extended User model for Citizens, Panchayat Staff, and Admins
    Adds additional fields for Indian government requirements
    """

    name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Full name of the user'
    )
    
    # Custom username validator to allow more characters
    username_validator = RegexValidator(
        regex=r'^[a-zA-Z0-9_]{4,20}$',
        message='Username must be 4-20 characters long and contain only letters, numbers, and underscore.',
    )
    
    username = models.CharField(
        max_length=20,
        unique=True,
        validators=[username_validator],
        help_text='Required. 4-20 characters. Letters, numbers, and underscore only.',
    )
    
    ROLE_CHOICES = (
        ('citizen', 'Citizen'),
        ('staff', 'Panchayat Staff'),
        ('admin', 'Admin'),
    )

    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    
    # Personal Information
    phone_regex = RegexValidator(
        regex=r'^[6-9]\d{9}$',
        message="Phone number must be 10 digits starting with 6-9"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=10,
        unique=True,
        help_text="10-digit mobile number"
    )
    
    aadhar_regex = RegexValidator(
        regex=r'^\d{12}$',
        message="Aadhar must be exactly 12 digits"
    )
    aadhar_number = models.CharField(
        validators=[aadhar_regex],
        max_length=12,
        unique=True,
        blank=True,
        null=True,
        help_text="12-digit Aadhar number"
    )
    
    date_of_birth = models.DateField(null=True, blank=True)

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        default='',
        help_text='Gender declared by user'
    )
    
    # Address Information
    address = models.TextField(help_text="Complete address")
    village = models.CharField(max_length=100, default="Model Village")
    taluka = models.CharField(max_length=100, default="Model Taluka")
    district = models.CharField(max_length=100, default="Model District")
    state = models.CharField(max_length=100, default="Maharashtra")
    pincode_regex = RegexValidator(
        regex=r'^\d{6}$',
        message="Pincode must be 6 digits"
    )
    pincode = models.CharField(
        validators=[pincode_regex],
        max_length=6,
        help_text="6-digit pincode"
    )
    
    # Profile Photo
    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True,
        help_text='Upload a profile photo'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    
    # Email Verification Fields (OTP-based)
    email_verified = models.BooleanField(
        default=False,
        help_text="Whether user's email has been verified via OTP"
    )
    
    email_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When email was verified"
    )
    
    # Account activation - user can only login after email verification
    is_active = models.BooleanField(
        default=False,
        help_text="Account is active only after email verification"
    )
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-created_at']
    
    def __str__(self):
        display_name = self.get_full_name()
        return f"{display_name} ({self.username})" if display_name else self.username
    
    def get_full_name(self):
        if self.name:
            return self.name.strip()

        return f"{self.first_name} {self.last_name}".strip() or self.username


# ============================================
# BASE APPLICATION MODEL
# ============================================

class Application(models.Model):
    """
    Base model to track all types of applications
    Acts as a central tracking system
    """
    
    APPLICATION_TYPES = (
        ('birth_certificate', 'Birth Certificate'),
        ('death_certificate', 'Death Certificate'),
        ('income_certificate', 'Income Certificate'),
        ('complaint_submission', 'Complaint Submission'),
        ('bill_request', 'Bill Related Request'),
        ('water_tax', 'Water Tax'),
        ('house_tax', 'House Tax'),
    )

    EMAIL_DELIVERY_STATUS = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    application_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )
    applicant = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    application_type = models.CharField(max_length=20, choices=APPLICATION_TYPES)
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Tracking
    applied_date = models.DateTimeField(auto_now_add=True)
    reviewed_date = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )
    
    # Admin remarks
    admin_remarks = models.TextField(blank=True, null=True)

    # Generated certificate / approval document
    certificate_pdf = models.FileField(
        upload_to='certificates/generated/%Y/%m/',
        blank=True,
        null=True,
        help_text='System-generated certificate or approval PDF'
    )

    # Email delivery tracking
    email_delivery_status = models.CharField(
        max_length=10,
        choices=EMAIL_DELIVERY_STATUS,
        default='pending'
    )
    approval_email_sent_at = models.DateTimeField(null=True, blank=True)
    email_delivery_error = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Application"
        verbose_name_plural = "Applications"
        ordering = ['-applied_date']
        indexes = [
            models.Index(fields=['application_number']),
            models.Index(fields=['status']),
            models.Index(fields=['applicant', 'status']),
        ]
    
    def __str__(self):
        return f"{self.application_number} - {self.get_application_type_display()}"
    
    def save(self, *args, **kwargs):
        if not self.application_number:
            # Generate unique application number
            prefix = self.application_type[:4].upper()
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.application_number = f"GP{prefix}{timestamp}"
        super().save(*args, **kwargs)


# ============================================
# BIRTH CERTIFICATE
# ============================================

class BirthCertificate(models.Model):
    """
    Birth Certificate Application Model
    """
    
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name='birth_certificate'
    )
    
    # Child Information
    child_name = models.CharField(max_length=200)
    child_gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=200)
    
    # Parent Information
    father_name = models.CharField(max_length=200)
    father_aadhar = models.CharField(max_length=12, blank=True)
    mother_name = models.CharField(max_length=200)
    mother_aadhar = models.CharField(max_length=12, blank=True)
    
    # Address at time of birth
    permanent_address = models.TextField()
    
    # Documents
    hospital_certificate = models.FileField(
        upload_to='birth_certificates/hospital/',
        help_text="Hospital/Doctor certificate"
    )
    parents_id_proof = models.FileField(
        upload_to='birth_certificates/id_proof/',
        help_text="Parents ID proof"
    )
    
    # Certificate Details (filled after approval)
    certificate_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True
    )
    issued_date = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Birth Certificate"
        verbose_name_plural = "Birth Certificates"
        ordering = ['-application__applied_date']
    
    def __str__(self):
        return f"Birth Certificate - {self.child_name}"


# ============================================
# DEATH CERTIFICATE
# ============================================

class DeathCertificate(models.Model):
    """
    Death Certificate Application Model
    """
    
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name='death_certificate'
    )
    
    # Deceased Information
    deceased_name = models.CharField(max_length=200)
    deceased_gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    deceased_age = models.IntegerField(validators=[MinValueValidator(0)])
    date_of_death = models.DateField()
    place_of_death = models.CharField(max_length=200)
    cause_of_death = models.TextField()
    
    # Informant (person applying)
    informant_name = models.CharField(max_length=200)
    informant_relation = models.CharField(max_length=100)
    informant_phone = models.CharField(max_length=10)
    
    # Address of deceased
    permanent_address = models.TextField()
    
    # Documents
    hospital_certificate = models.FileField(
        upload_to='death_certificates/hospital/',
        help_text="Hospital/Doctor certificate or Panchnama",
        blank=True,
        null=True
    )
    deceased_id_proof = models.FileField(
        upload_to='death_certificates/id_proof/',
        help_text="Deceased person's ID proof"
    )
    
    # Certificate Details (filled after approval)
    certificate_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True
    )
    issued_date = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Death Certificate"
        verbose_name_plural = "Death Certificates"
        ordering = ['-application__applied_date']
    
    def __str__(self):
        return f"Death Certificate - {self.deceased_name}"


# ============================================
# INCOME CERTIFICATE
# ============================================

class IncomeCertificate(models.Model):
    """
    Income Certificate Application Model
    """
    
    INCOME_SOURCE_CHOICES = (
        ('agriculture', 'Agriculture'),
        ('business', 'Business'),
        ('salary', 'Salary/Employment'),
        ('pension', 'Pension'),
        ('other', 'Other'),
    )
    
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name='income_certificate'
    )
    
    # Applicant Information (can be different from user)
    applicant_name = models.CharField(max_length=200)
    father_husband_name = models.CharField(max_length=200)
    occupation = models.CharField(max_length=200)
    
    # Income Details
    annual_income = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    income_source = models.CharField(max_length=20, choices=INCOME_SOURCE_CHOICES)
    income_details = models.TextField(
        help_text="Detailed description of income sources"
    )
    
    # Purpose
    purpose_of_certificate = models.TextField(
        help_text="Why do you need this certificate?"
    )
    
    # Address
    residential_address = models.TextField()
    
    # Documents
    income_proof = models.FileField(
        upload_to='income_certificates/income_proof/',
        help_text="Salary slip, Form 16, or other income proof"
    )
    id_proof = models.FileField(
        upload_to='income_certificates/id_proof/',
        help_text="Aadhar or other ID proof"
    )
    ration_card = models.FileField(
        upload_to='income_certificates/ration_card/',
        blank=True,
        null=True,
        help_text="Ration card (if available)"
    )
    
    # Certificate Details (filled after approval)
    certificate_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True
    )
    issued_date = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Income Certificate"
        verbose_name_plural = "Income Certificates"
        ordering = ['-application__applied_date']
    
    def __str__(self):
        return f"Income Certificate - {self.applicant_name}"


# ============================================
# TAX PAYMENT
# ============================================

class TaxPayment(models.Model):
    """
    Tax Payment Model for Water Tax and House Tax
    """
    
    TAX_TYPE_CHOICES = (
        ('water_tax', 'Water Tax'),
        ('house_tax', 'House Tax'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('online', 'Online'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('dd', 'Demand Draft'),
    )
    
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name='tax_payment'
    )
    
    # Tax Details
    tax_type = models.CharField(max_length=15, choices=TAX_TYPE_CHOICES)
    
    # Property Details
    property_number = models.CharField(max_length=50)
    property_address = models.TextField()
    property_area_sqft = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Financial Year
    financial_year = models.CharField(
        max_length=10,
        help_text="e.g., 2025-26"
    )
    
    # Tax Amount
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    late_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Payment Details
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True
    )
    payment_date = models.DateTimeField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    receipt_number = models.CharField(
        max_length=50,
        blank=True,
        unique=True
    )
    
    # Documents
    property_document = models.FileField(
        upload_to='tax_payments/property_docs/',
        help_text="Property ownership proof",
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Tax Payment"
        verbose_name_plural = "Tax Payments"
        ordering = ['-application__applied_date']
        indexes = [
            models.Index(fields=['property_number']),
            models.Index(fields=['payment_status']),
        ]
    
    def __str__(self):
        return f"{self.get_tax_type_display()} - {self.property_number}"
    
    def save(self, *args, **kwargs):
        # Calculate total amount
        self.total_amount = self.tax_amount + self.late_fee
        
        # Generate receipt number if paid
        if self.payment_status == 'paid' and not self.receipt_number:
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.receipt_number = f"RCP{timestamp}"
        
        super().save(*args, **kwargs)


# ============================================
# ELECTRICITY BILL SERVICE
# ============================================

class ElectricityBill(models.Model):
    """Electricity bill records for citizen self-service."""

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='electricity_bills'
    )
    consumer_number = models.CharField(max_length=30)
    bill_month = models.CharField(max_length=7, help_text='Format: YYYY-MM')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    due_date = models.DateField()
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=120, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Electricity Bill'
        verbose_name_plural = 'Electricity Bills'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['user', 'payment_status']),
            models.Index(fields=['consumer_number']),
            models.Index(fields=['bill_month']),
        ]
        unique_together = ('user', 'consumer_number', 'bill_month')

    def __str__(self):
        return f"{self.consumer_number} - {self.bill_month}"


# ============================================
# WATER BILL SERVICE
# ============================================

class WaterBill(models.Model):
    """Water bill records for citizen self-service."""

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='water_bills'
    )
    connection_number = models.CharField(max_length=30)
    bill_month = models.CharField(max_length=7, help_text='Format: YYYY-MM')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    due_date = models.DateField()
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=120, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Water Bill'
        verbose_name_plural = 'Water Bills'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['user', 'payment_status']),
            models.Index(fields=['connection_number']),
            models.Index(fields=['bill_month']),
        ]
        unique_together = ('user', 'connection_number', 'bill_month')

    def __str__(self):
        return f"{self.connection_number} - {self.bill_month}"


# ============================================
# PROPERTY / HOUSE TAX SERVICE
# ============================================

class PropertyTaxRecord(models.Model):
    """Property tax records with basic automatic tax calculation."""

    PROPERTY_TYPE_CHOICES = (
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='property_tax_records'
    )
    property_number = models.CharField(max_length=50)
    owner_name = models.CharField(max_length=200)
    property_address = models.TextField()
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, default='residential')
    built_up_area_sqft = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    tax_rate_per_sqft = models.DecimalField(max_digits=8, decimal_places=2, default=1.50, validators=[MinValueValidator(0)])
    tax_year = models.CharField(max_length=9, help_text='Format: YYYY-YY')
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    due_date = models.DateField()
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Property Tax Record'
        verbose_name_plural = 'Property Tax Records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'payment_status']),
            models.Index(fields=['property_number']),
            models.Index(fields=['tax_year']),
        ]
        unique_together = ('user', 'property_number', 'tax_year')

    def __str__(self):
        return f"{self.property_number} ({self.tax_year})"

    def save(self, *args, **kwargs):
        # Basic tax calculation: area x rate
        self.tax_amount = self.built_up_area_sqft * self.tax_rate_per_sqft
        super().save(*args, **kwargs)


# ============================================
# COMPLAINT MANAGEMENT
# ============================================

class Complaint(models.Model):
    """
    Complaint/Grievance Management Model
    """
    
    CATEGORY_CHOICES = (
        ('water_supply', 'Water Supply'),
        ('electricity', 'Electricity'),
        ('road', 'Road & Infrastructure'),
        ('sanitation', 'Sanitation'),
        ('street_light', 'Street Light'),
        ('drainage', 'Drainage'),
        ('waste_management', 'Waste Management'),
        ('other', 'Other'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    
    # Complaint Details
    complaint_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )
    complainant = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='complaints'
    )
    application = models.OneToOneField(
        'Application',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaint_record'
    )
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=300)
    description = models.TextField()
    location = models.TextField(help_text="Location of the issue")
    
    # Priority & Status
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='open'
    )
    
    # Attachments
    complaint_photo = models.ImageField(
        upload_to='complaints/photos/',
        blank=True,
        null=True,
        help_text="Photo evidence of the issue"
    )
    
    # Tracking
    filed_date = models.DateTimeField(auto_now_add=True)
    assigned_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints'
    )
    resolved_date = models.DateTimeField(null=True, blank=True)
    
    # Resolution
    resolution_remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Complaint"
        verbose_name_plural = "Complaints"
        ordering = ['-filed_date']
        indexes = [
            models.Index(fields=['complaint_number']),
            models.Index(fields=['status']),
            models.Index(fields=['complainant', 'status']),
        ]
    
    def __str__(self):
        return f"{self.complaint_number} - {self.subject}"
    
    def save(self, *args, **kwargs):
        if not self.complaint_number:
            # Generate unique complaint number
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.complaint_number = f"CMP{timestamp}"
        super().save(*args, **kwargs)


class BillRequest(models.Model):
    """Citizen bill-related service request tracked under Application."""

    REQUEST_TYPES = (
        ('electricity', 'Electricity Bill'),
        ('water', 'Water Bill'),
        ('property_tax', 'Property Tax'),
        ('other', 'Other Bill Request'),
    )

    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name='bill_request'
    )
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    account_or_consumer_number = models.CharField(max_length=60)
    subject = models.CharField(max_length=200)
    details = models.TextField()
    attachment = models.FileField(
        upload_to='bill_requests/attachments/',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Bill Request'
        verbose_name_plural = 'Bill Requests'
        ordering = ['-application__applied_date']

    def __str__(self):
        return f"{self.get_request_type_display()} - {self.application.application_number}"


# ============================================
# APPLICATION STATUS HISTORY
# ============================================

class ApplicationStatusHistory(models.Model):
    """
    Track status changes of applications for audit trail
    """
    
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    
    old_status = models.CharField(max_length=15)
    new_status = models.CharField(max_length=15)
    
    changed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Status History"
        verbose_name_plural = "Status Histories"
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.application.application_number}: {self.old_status} → {self.new_status}"


# ============================================
# COMPLAINT STATUS HISTORY
# ============================================

class ComplaintHistory(models.Model):
    """
    Track all updates and changes to complaints for audit trail
    """
    
    ACTION_CHOICES = (
        ('created', 'Complaint Created'),
        ('assigned', 'Assigned to Staff'),
        ('status_changed', 'Status Changed'),
        ('priority_changed', 'Priority Changed'),
        ('updated', 'Updated'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    
    complaint = models.ForeignKey(
        'Complaint',
        on_delete=models.CASCADE,
        related_name='history'
    )
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    old_value = models.CharField(max_length=100, blank=True, null=True)
    new_value = models.CharField(max_length=100, blank=True, null=True)
    
    performed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True
    )
    performed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Complaint History"
        verbose_name_plural = "Complaint Histories"
        ordering = ['-performed_at']
    
    def __str__(self):
        return f"{self.complaint.complaint_number}: {self.get_action_display()} by {self.performed_by}"


# ============================================
# USER NOTIFICATIONS
# ============================================

class Notification(models.Model):
    """
    Notification model for citizen/staff/admin updates.
    """

    CATEGORY_CHOICES = (
        ('application', 'Application'),
        ('certificate', 'Certificate'),
        ('complaint', 'Complaint'),
        ('bill', 'Bill'),
        ('system', 'System'),
    )

    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=120)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='system')
    target_url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.recipient.username}: {self.title}"


# ============================================
# USER ACTIVITY HISTORY
# ============================================

class UserActivity(models.Model):
    """
    Audit-style activity history for user actions.
    """

    ACTION_CHOICES = (
        ('application_submitted', 'Application Submitted'),
        ('application_updated', 'Application Updated'),
        ('application_approved', 'Application Approved'),
        ('application_rejected', 'Application Rejected'),
        ('complaint_submitted', 'Complaint Submitted'),
        ('complaint_updated', 'Complaint Updated'),
        ('payment_recorded', 'Payment Recorded'),
        ('document_downloaded', 'Document Downloaded'),
        ('profile_updated', 'Profile Updated'),
        ('password_changed', 'Password Changed'),
        ('account_deleted', 'Account Deleted'),
        ('user_managed', 'User Managed'),
        ('login', 'Login'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )
    action = models.CharField(max_length=40, choices=ACTION_CHOICES, default='other')
    description = models.CharField(max_length=255)
    application = models.ForeignKey(
        Application,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    reference = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.action}"


# ============================================
# PENDING CITIZEN REGISTRATION (OTP-FIRST)
# ============================================

class PendingRegistration(models.Model):
    """Temporary citizen registration data stored until email OTP is verified."""

    OTP_LENGTH = 6
    OTP_MAX_ATTEMPTS = 3
    OTP_EXPIRY_SECONDS = 5 * 60

    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    username_validator = RegexValidator(
        regex=r'^[a-zA-Z0-9_]{4,20}$',
        message='Username must be 4-20 characters long and contain only letters, numbers, and underscore.',
    )

    name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True, default='')
    username = models.CharField(max_length=20, unique=True, validators=[username_validator])
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=10, unique=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    address = models.TextField()
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)
    aadhar_number = models.CharField(max_length=12, blank=True, default='')
    profile_photo = models.ImageField(upload_to='pending_profiles/', blank=True, null=True)

    password_hash = models.CharField(max_length=128)

    otp_code_hash = models.CharField(max_length=128)
    otp_expires_at = models.DateTimeField()
    otp_attempts = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_otp_sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'created_at']),
            models.Index(fields=['phone_number', 'created_at']),
        ]

    def __str__(self):
        return f"Pending registration: {self.email}"

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def set_otp(self, raw_otp):
        raw_otp = str(raw_otp).strip()
        self.otp_code_hash = make_password(raw_otp)
        self.otp_attempts = 0
        self.otp_expires_at = timezone.now() + timedelta(seconds=self.OTP_EXPIRY_SECONDS)
        self.last_otp_sent_at = timezone.now()

    def verify_otp(self, raw_otp):
        raw_otp = str(raw_otp).strip()
        if self.is_verified:
            return False
        if self.is_expired() or self.otp_attempts >= self.OTP_MAX_ATTEMPTS:
            return False

        self.otp_attempts += 1
        self.save(update_fields=['otp_attempts'])
        return check_password(raw_otp, self.otp_code_hash)

    def is_expired(self):
        return timezone.now() > self.otp_expires_at

    def get_time_remaining(self):
        if self.is_expired():
            return 0
        return int((self.otp_expires_at - timezone.now()).total_seconds())


# ============================================
# OTP EMAIL VERIFICATION MODEL
# ============================================

class EmailOTP(models.Model):
    """
    One-Time Password (OTP) for Email Verification
    
    Security Features:
    - 6-digit random OTP
    - 1-minute expiration
    - One-time use only
    - Tracks verification attempts
    """
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='email_otps'
    )
    
    email = models.EmailField(
        help_text="Email address where OTP was sent"
    )
    
    otp_code = models.CharField(
        max_length=6,
        help_text="Masked OTP code"
    )

    otp_code_hash = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Hashed OTP value for secure verification"
    )
    
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether this OTP has been successfully verified"
    )
    
    is_used = models.BooleanField(
        default=False,
        help_text="Whether this OTP has been used (one-time use)"
    )
    
    verification_attempts = models.IntegerField(
        default=0,
        help_text="Number of verification attempts (max 3)"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When OTP was generated"
    )
    
    expires_at = models.DateTimeField(
        help_text="When OTP expires (1 minute from creation)"
    )
    
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When OTP was successfully verified"
    )
    
    class Meta:
        verbose_name = "Email OTP"
        verbose_name_plural = "Email OTPs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_verified']),
            models.Index(fields=['email', 'otp_code']),
        ]
    
    def __str__(self):
        status = "Verified" if self.is_verified else "Pending"
        return f"OTP for {self.email} - {status}"
    
    def is_valid(self):
        """
        Check if OTP is still valid
        Returns True if OTP is not expired, not used, and attempts < 3
        """
        from django.utils import timezone
        
        if self.is_used:
            return False
        
        if self.is_verified:
            return False
        
        if self.verification_attempts >= 3:
            return False
        
        if timezone.now() > self.expires_at:
            return False
        
        return True
    
    def increment_attempts(self):
        """Increment verification attempts"""
        self.verification_attempts += 1
        self.save(update_fields=['verification_attempts'])

    def set_otp_code(self, raw_otp):
        """Store masked OTP and hashed OTP (never plain OTP at rest)."""
        self.otp_code = f"****{raw_otp[-2:]}"
        self.otp_code_hash = make_password(raw_otp)

    def verify_otp_code(self, raw_otp):
        """Verify OTP securely with hash; fallback supports legacy plaintext rows."""
        if self.otp_code_hash:
            return check_password(raw_otp, self.otp_code_hash)
        return self.otp_code == raw_otp
    
    def mark_as_verified(self):
        """Mark OTP as verified and used"""
        from django.utils import timezone
        
        self.is_verified = True
        self.is_used = True
        self.verified_at = timezone.now()
        self.save(update_fields=['is_verified', 'is_used', 'verified_at'])
    
    def get_time_remaining(self):
        """Get remaining time in seconds"""
        from django.utils import timezone
        
        if timezone.now() > self.expires_at:
            return 0
        
        delta = self.expires_at - timezone.now()
        return int(delta.total_seconds())
    
    def save(self, *args, **kwargs):
        """
        Override save to set expiration time
        OTP expires 1 minute after creation
        """
        if not self.pk and not self.expires_at:
            from django.utils import timezone
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(minutes=1)
        
        super().save(*args, **kwargs)

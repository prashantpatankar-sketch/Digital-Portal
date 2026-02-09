# 🔷 Django Models Reference - Quick Guide

## Model Relationships Overview

```python
# portal_app/models.py

# ============================================
# USER MODEL
# ============================================
CustomUser (AbstractUser)
├── role: citizen/staff/admin
├── phone_number (unique)
├── aadhar_number (unique, optional)
├── address, village, pincode
└── Relationships:
    ├── applications (1:N) → Application
    ├── reviewed_applications (1:N) → Application
    ├── complaints (1:N) → Complaint
    └── assigned_complaints (1:N) → Complaint


# ============================================
# APPLICATION TRACKER
# ============================================
Application
├── application_number (auto-generated, unique)
├── applicant → CustomUser (FK)
├── reviewed_by → CustomUser (FK, nullable)
├── type: birth/death/income/water_tax/house_tax
├── status: pending/under_review/approved/rejected
└── Relationships:
    ├── birth_certificate (1:1) → BirthCertificate
    ├── death_certificate (1:1) → DeathCertificate
    ├── income_certificate (1:1) → IncomeCertificate
    ├── tax_payment (1:1) → TaxPayment
    └── status_history (1:N) → ApplicationStatusHistory


# ============================================
# CERTIFICATE MODELS
# ============================================
BirthCertificate
├── application → Application (1:1, FK)
├── child_name, child_gender, date_of_birth
├── father_name, mother_name
├── hospital_certificate (file)
├── parents_id_proof (file)
└── certificate_number (after approval)

DeathCertificate
├── application → Application (1:1, FK)
├── deceased_name, deceased_age
├── date_of_death, cause_of_death
├── informant_name, informant_relation
├── hospital_certificate (file)
└── certificate_number (after approval)

IncomeCertificate
├── application → Application (1:1, FK)
├── applicant_name, occupation
├── annual_income, income_source
├── income_proof (file)
├── id_proof (file)
└── certificate_number, valid_until (after approval)


# ============================================
# TAX & COMPLAINTS
# ============================================
TaxPayment
├── application → Application (1:1, FK)
├── tax_type: water_tax/house_tax
├── property_number, property_address
├── tax_amount, late_fee, total_amount
├── payment_status, payment_method
└── receipt_number (auto-generated when paid)

Complaint
├── complaint_number (auto-generated, unique)
├── complainant → CustomUser (FK)
├── assigned_to → CustomUser (FK, nullable)
├── category: water_supply/road/sanitation/etc
├── status: open/in_progress/resolved/closed
├── priority: low/medium/high/urgent
└── complaint_photo (file, optional)


# ============================================
# AUDIT TRAIL
# ============================================
ApplicationStatusHistory
├── application → Application (FK)
├── changed_by → CustomUser (FK, nullable)
├── old_status → new_status
├── changed_at (timestamp)
└── remarks
```

---

## Complete Django Models Code

```python
"""
portal_app/models.py
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone


# ============================================
# CUSTOM USER MODEL
# ============================================

class CustomUser(AbstractUser):
    """User model with role-based access"""
    
    ROLE_CHOICES = (
        ('citizen', 'Citizen'),
        ('staff', 'Panchayat Staff'),
        ('admin', 'Admin'),
    )
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='citizen'
    )
    
    # Validators
    phone_regex = RegexValidator(
        regex=r'^[6-9]\d{9}$',
        message="Phone: 10 digits, starts with 6-9"
    )
    aadhar_regex = RegexValidator(
        regex=r'^\d{12}$',
        message="Aadhar: exactly 12 digits"
    )
    pincode_regex = RegexValidator(
        regex=r'^\d{6}$',
        message="Pincode: exactly 6 digits"
    )
    
    # Fields
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=10,
        unique=True
    )
    aadhar_number = models.CharField(
        validators=[aadhar_regex],
        max_length=12,
        unique=True,
        blank=True,
        null=True
    )
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField()
    village = models.CharField(max_length=100, default="Model Village")
    taluka = models.CharField(max_length=100, default="Model Taluka")
    district = models.CharField(max_length=100, default="Model District")
    state = models.CharField(max_length=100, default="Maharashtra")
    pincode = models.CharField(validators=[pincode_regex], max_length=6)
    profile_photo = models.FileField(
        upload_to='profile_photos/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"


# ============================================
# APPLICATION TRACKER
# ============================================

class Application(models.Model):
    """Central application tracking"""
    
    APPLICATION_TYPES = (
        ('birth_certificate', 'Birth Certificate'),
        ('death_certificate', 'Death Certificate'),
        ('income_certificate', 'Income Certificate'),
        ('water_tax', 'Water Tax'),
        ('house_tax', 'House Tax'),
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
    application_type = models.CharField(
        max_length=20,
        choices=APPLICATION_TYPES
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending'
    )
    applied_date = models.DateTimeField(auto_now_add=True)
    reviewed_date = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )
    admin_remarks = models.TextField(blank=True, null=True)
    
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
            prefix = self.application_type[:4].upper()
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.application_number = f"GP{prefix}{timestamp}"
        super().save(*args, **kwargs)


# ============================================
# CERTIFICATES
# ============================================

class BirthCertificate(models.Model):
    """Birth certificate details"""
    
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
    child_name = models.CharField(max_length=200)
    child_gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=200)
    father_name = models.CharField(max_length=200)
    father_aadhar = models.CharField(max_length=12, blank=True)
    mother_name = models.CharField(max_length=200)
    mother_aadhar = models.CharField(max_length=12, blank=True)
    permanent_address = models.TextField()
    hospital_certificate = models.FileField(
        upload_to='birth_certificates/hospital/'
    )
    parents_id_proof = models.FileField(
        upload_to='birth_certificates/id_proof/'
    )
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


class DeathCertificate(models.Model):
    """Death certificate details"""
    
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
    deceased_name = models.CharField(max_length=200)
    deceased_gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    deceased_age = models.IntegerField(validators=[MinValueValidator(0)])
    date_of_death = models.DateField()
    place_of_death = models.CharField(max_length=200)
    cause_of_death = models.TextField()
    informant_name = models.CharField(max_length=200)
    informant_relation = models.CharField(max_length=100)
    informant_phone = models.CharField(max_length=10)
    permanent_address = models.TextField()
    hospital_certificate = models.FileField(
        upload_to='death_certificates/hospital/',
        blank=True,
        null=True
    )
    deceased_id_proof = models.FileField(
        upload_to='death_certificates/id_proof/'
    )
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


class IncomeCertificate(models.Model):
    """Income certificate details"""
    
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
    applicant_name = models.CharField(max_length=200)
    father_husband_name = models.CharField(max_length=200)
    occupation = models.CharField(max_length=200)
    annual_income = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    income_source = models.CharField(max_length=20, choices=INCOME_SOURCE_CHOICES)
    income_details = models.TextField()
    purpose_of_certificate = models.TextField()
    residential_address = models.TextField()
    income_proof = models.FileField(upload_to='income_certificates/income_proof/')
    id_proof = models.FileField(upload_to='income_certificates/id_proof/')
    ration_card = models.FileField(
        upload_to='income_certificates/ration_card/',
        blank=True,
        null=True
    )
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
    """Water and house tax payments"""
    
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
    tax_type = models.CharField(max_length=15, choices=TAX_TYPE_CHOICES)
    property_number = models.CharField(max_length=50)
    property_address = models.TextField()
    property_area_sqft = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    financial_year = models.CharField(max_length=10)
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
    receipt_number = models.CharField(max_length=50, blank=True, unique=True)
    property_document = models.FileField(
        upload_to='tax_payments/property_docs/',
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
        self.total_amount = self.tax_amount + self.late_fee
        if self.payment_status == 'paid' and not self.receipt_number:
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.receipt_number = f"RCP{timestamp}"
        super().save(*args, **kwargs)


# ============================================
# COMPLAINTS
# ============================================

class Complaint(models.Model):
    """Complaint/grievance management"""
    
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
    
    complaint_number = models.CharField(max_length=20, unique=True, editable=False)
    complainant = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='complaints'
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=300)
    description = models.TextField()
    location = models.TextField()
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
    complaint_photo = models.ImageField(
        upload_to='complaints/photos/',
        blank=True,
        null=True
    )
    filed_date = models.DateTimeField(auto_now_add=True)
    assigned_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints'
    )
    resolved_date = models.DateTimeField(null=True, blank=True)
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
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.complaint_number = f"CMP{timestamp}"
        super().save(*args, **kwargs)


# ============================================
# AUDIT TRAIL
# ============================================

class ApplicationStatusHistory(models.Model):
    """Application status change history"""
    
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
```

---

## Migration Commands

```bash
# 1. Create migrations
python manage.py makemigrations

# 2. Show SQL that will be executed
python manage.py sqlmigrate portal_app 0001

# 3. Apply migrations
python manage.py migrate

# 4. Check migration status
python manage.py showmigrations

# 5. Verify tables
python manage.py dbshell
```

---

## Query Examples

```python
# Get user's applications
user = CustomUser.objects.get(username='ramesh')
apps = user.applications.all()

# Get application with certificate
app = Application.objects.get(application_number='GPBIRT...')
birth_cert = app.birth_certificate

# Get all pending applications with applicant info
pending = Application.objects.filter(
    status='pending'
).select_related('applicant')

# Get complaints with assigned staff
complaints = Complaint.objects.filter(
    status='open'
).select_related('assigned_to')

# Get application history
app = Application.objects.get(pk=1)
history = app.status_history.all()

# Count by status
from django.db.models import Count
stats = Application.objects.values('status').annotate(
    count=Count('id')
)
```

---

**Models Status**: ✅ Production Ready  
**Total Models**: 8  
**Relationships**: Properly defined with ForeignKeys  
**Validation**: Implemented at model level  
**Indexes**: Optimized for common queries

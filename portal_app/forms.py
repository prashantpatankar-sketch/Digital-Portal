"""
Django Forms for Gram Panchayat Portal

Contains all forms for:
- User Registration & Login
- Birth, Death, Income Certificate Applications
- Tax Payments
- Complaint Filing
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div
from .models import (
    CustomUser, BirthCertificate, DeathCertificate, 
    IncomeCertificate, TaxPayment, Complaint, Application
)


# ============================================
# USER AUTHENTICATION FORMS
# ============================================

class CitizenRegistrationForm(UserCreationForm):
    """
    Citizen Registration Form with all required fields
    """
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    
    phone_number = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '10-digit mobile number'
        })
    )
    
    aadhar_number = forms.CharField(
        max_length=12,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12-digit Aadhar number'
        })
    )
    
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Complete address'
        })
    )
    
    village = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Village name'
        })
    )
    
    pincode = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '6-digit pincode'
        })
    )
    
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        required=True,
        initial='citizen',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text='Select your role. Note: Admin and Staff roles require approval.'
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'phone_number', 'aadhar_number', 'date_of_birth',
            'address', 'village', 'pincode', 'role', 'password1', 'password2'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password (min 8 characters)'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    
    def clean_email(self):
        """Ensure email is unique"""
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
    def clean_phone_number(self):
        """Ensure phone number is unique and valid"""
        phone = self.cleaned_data.get('phone_number')
        if CustomUser.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("This phone number is already registered.")
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError("Phone number must be exactly 10 digits.")
        if not phone.startswith(('6', '7', '8', '9')):
            raise forms.ValidationError("Phone number must start with 6, 7, 8, or 9.")
        return phone
    
    def clean_aadhar_number(self):
        """Ensure Aadhar is unique if provided"""
        aadhar = self.cleaned_data.get('aadhar_number')
        if aadhar:
            if not aadhar.isdigit() or len(aadhar) != 12:
                raise forms.ValidationError("Aadhar number must be exactly 12 digits.")
            if CustomUser.objects.filter(aadhar_number=aadhar).exists():
                raise forms.ValidationError("This Aadhar number is already registered.")
        return aadhar
    
    def clean_pincode(self):
        """Validate pincode format"""
        pincode = self.cleaned_data.get('pincode')
        if pincode:
            if not pincode.isdigit() or len(pincode) != 6:
                raise forms.ValidationError("Pincode must be exactly 6 digits.")
        return pincode
    
    def clean_username(self):
        """Validate username - allows letters, numbers, @, dot, +, -, underscore"""
        import re
        username = self.cleaned_data.get('username')
        # Allow alphanumeric, @, dot, plus, minus, underscore
        if not re.match(r'^[\w.@+-]+$', username):
            raise forms.ValidationError("Username can only contain letters, numbers, @, dot, plus, minus, and underscore.")
        return username


class UserLoginForm(AuthenticationForm):
    """
    Custom Login Form
    """
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Email'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


# ============================================
# CERTIFICATE APPLICATION FORMS
# ============================================

class BirthCertificateForm(forms.ModelForm):
    """
    Birth Certificate Application Form
    """
    
    class Meta:
        model = BirthCertificate
        fields = [
            'child_name', 'child_gender', 'date_of_birth', 'place_of_birth',
            'father_name', 'father_aadhar', 'mother_name', 'mother_aadhar',
            'permanent_address', 'hospital_certificate', 'parents_id_proof'
        ]
        widgets = {
            'child_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name of child'
            }),
            'child_gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'place_of_birth': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Hospital/Home name and location'
            }),
            'father_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Father's full name"
            }),
            'father_aadhar': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12-digit Aadhar number'
            }),
            'mother_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Mother's full name"
            }),
            'mother_aadhar': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12-digit Aadhar number'
            }),
            'permanent_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Complete permanent address'
            }),
            'hospital_certificate': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'parents_id_proof': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }
    
    def clean_father_aadhar(self):
        """Validate father's Aadhar number"""
        aadhar = self.cleaned_data.get('father_aadhar')
        if aadhar and (not aadhar.isdigit() or len(aadhar) != 12):
            raise forms.ValidationError("Father's Aadhar must be exactly 12 digits.")
        return aadhar
    
    def clean_mother_aadhar(self):
        """Validate mother's Aadhar number"""
        aadhar = self.cleaned_data.get('mother_aadhar')
        if aadhar and (not aadhar.isdigit() or len(aadhar) != 12):
            raise forms.ValidationError("Mother's Aadhar must be exactly 12 digits.")
        return aadhar
    
    def clean_hospital_certificate(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('hospital_certificate')
        if file:
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be less than 5MB.")
            # Check file extension
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
            import os
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError("Only PDF, JPG, JPEG, and PNG files are allowed.")
        return file
    
    def clean_parents_id_proof(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('parents_id_proof')
        if file:
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be less than 5MB.")
            # Check file extension
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
            import os
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError("Only PDF, JPG, JPEG, and PNG files are allowed.")
        return file


class DeathCertificateForm(forms.ModelForm):
    """
    Death Certificate Application Form
    """
    
    class Meta:
        model = DeathCertificate
        fields = [
            'deceased_name', 'deceased_gender', 'deceased_age',
            'date_of_death', 'place_of_death', 'cause_of_death',
            'informant_name', 'informant_relation', 'informant_phone',
            'permanent_address', 'hospital_certificate', 'deceased_id_proof'
        ]
        widgets = {
            'deceased_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name of deceased'
            }),
            'deceased_gender': forms.Select(attrs={'class': 'form-select'}),
            'deceased_age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Age at time of death'
            }),
            'date_of_death': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'place_of_death': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Location of death'
            }),
            'cause_of_death': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Brief description of cause'
            }),
            'informant_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'informant_relation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your relation with deceased'
            }),
            'informant_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10-digit mobile number'
            }),
            'permanent_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Permanent address of deceased'
            }),
            'hospital_certificate': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'deceased_id_proof': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }


class IncomeCertificateForm(forms.ModelForm):
    """
    Income Certificate Application Form
    """
    
    class Meta:
        model = IncomeCertificate
        fields = [
            'applicant_name', 'father_husband_name', 'occupation',
            'annual_income', 'income_source', 'income_details',
            'purpose_of_certificate', 'residential_address',
            'income_proof', 'id_proof', 'ration_card'
        ]
        widgets = {
            'applicant_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name'
            }),
            'father_husband_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Father/Husband name'
            }),
            'occupation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Current occupation'
            }),
            'annual_income': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Annual income in ₹',
                'step': '0.01'
            }),
            'income_source': forms.Select(attrs={'class': 'form-select'}),
            'income_details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detailed description of all income sources'
            }),
            'purpose_of_certificate': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Why do you need this certificate?'
            }),
            'residential_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Complete residential address'
            }),
            'income_proof': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'id_proof': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'ration_card': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }


# ============================================
# TAX PAYMENT FORM
# ============================================

class TaxPaymentForm(forms.ModelForm):
    """
    Tax Payment Form for Water and House Tax
    """
    
    class Meta:
        model = TaxPayment
        fields = [
            'tax_type', 'property_number', 'property_address',
            'property_area_sqft', 'financial_year', 'tax_amount',
            'late_fee', 'payment_method', 'property_document'
        ]
        widgets = {
            'tax_type': forms.Select(attrs={'class': 'form-select'}),
            'property_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Property/House number'
            }),
            'property_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Complete property address'
            }),
            'property_area_sqft': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Area in square feet',
                'step': '0.01'
            }),
            'financial_year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2025-26'
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tax amount in ₹',
                'step': '0.01'
            }),
            'late_fee': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Late fee (if any)',
                'step': '0.01'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'property_document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }


# ============================================
# COMPLAINT FORM
# ============================================

class ComplaintForm(forms.ModelForm):
    """
    Complaint/Grievance Filing Form
    """
    
    class Meta:
        model = Complaint
        fields = [
            'category', 'subject', 'description', 'location',
            'priority', 'complaint_photo'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief subject of complaint'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detailed description of the issue'
            }),
            'location': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Exact location of the issue'
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'complaint_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png'
            }),
        }


# ============================================
# ADMIN FORMS
# ============================================

class ApplicationReviewForm(forms.ModelForm):
    """
    Form for admins to review and update application status
    """
    
    class Meta:
        model = Application
        fields = ['status', 'admin_remarks']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add remarks for applicant'
            }),
        }


class ComplaintUpdateForm(forms.ModelForm):
    """
    Form for admins to update complaint status
    """
    
    class Meta:
        model = Complaint
        fields = ['status', 'priority', 'assigned_to', 'resolution_remarks']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'resolution_remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Resolution details'
            }),
        }


# ============================================
# OTP VERIFICATION FORMS
# ============================================

class OTPVerificationForm(forms.Form):
    """
    Form for OTP verification during email verification
    
    Security Features:
    - 6-digit numeric OTP only
    - No special characters allowed
    - Client-side and server-side validation
    """
    
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': 'Enter 6-digit OTP',
            'autocomplete': 'off',
            'inputmode': 'numeric',
            'pattern': '[0-9]{6}',
            'maxlength': '6',
            'style': 'letter-spacing: 0.5em; font-size: 1.5rem;'
        }),
        label='Enter OTP',
        help_text='Enter the 6-digit code sent to your email'
    )
    
    def clean_otp_code(self):
        """
        Validate OTP code format
        - Must be exactly 6 digits
        - Numeric characters only
        """
        otp_code = self.cleaned_data.get('otp_code', '').strip()
        
        # Check if exactly 6 characters
        if len(otp_code) != 6:
            raise forms.ValidationError("OTP must be exactly 6 digits.")
        
        # Check if all digits
        if not otp_code.isdigit():
            raise forms.ValidationError("OTP must contain only numbers.")
        
        return otp_code


class ResendOTPForm(forms.Form):
    """
    Form for resending OTP (CSRF protection)
    """
    pass  # No fields needed, just for CSRF validation

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
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from datetime import date
import re
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div
from .models import (
    CustomUser, BirthCertificate, DeathCertificate, 
    IncomeCertificate, TaxPayment, Complaint, Application, BillRequest,
    ElectricityBill, WaterBill, PropertyTaxRecord, PendingRegistration
)


# ============================================
# USER AUTHENTICATION FORMS
# ============================================

class CitizenRegistrationForm(forms.Form):
    """
    Government-grade citizen registration form (OTP-first flow).
    """

    username = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Choose a username'),
            'autocomplete': 'username',
            'maxlength': '20',
        })
    )

    name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your full name'),
            'autocomplete': 'name',
        })
    )

    gender = forms.ChoiceField(
        choices=(
            ('', 'Select gender'),
            ('male', _('Male')),
            ('female', _('Female')),
            ('other', _('Other')),
        ),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    date_of_birth = forms.DateField(
        required=True,
        input_formats=['%d-%m-%Y', '%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'text',
            'placeholder': _('DD-MM-YYYY'),
            'autocomplete': 'bday',
            'data-max-date': date.today().strftime('%d-%m-%Y'),
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter email address'),
            'autocomplete': 'email',
        })
    )

    phone_number = forms.CharField(
        required=True,
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('10-digit mobile number'),
            'maxlength': '10',
            'inputmode': 'numeric',
            'autocomplete': 'tel-national',
        })
    )

    address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('House no, street, landmark, area'),
            'autocomplete': 'street-address',
        })
    )

    state = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('State'),
            'autocomplete': 'address-level1',
        })
    )

    district = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('District'),
            'autocomplete': 'address-level2',
        })
    )

    pincode = forms.CharField(
        max_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('6-digit pincode'),
            'maxlength': '6',
            'inputmode': 'numeric',
            'autocomplete': 'postal-code',
        })
    )

    aadhar_number = forms.CharField(
        max_length=12,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Optional 12-digit Aadhaar number'),
            'maxlength': '12',
            'inputmode': 'numeric',
        })
    )

    profile_photo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
        })
    )

    password1 = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Create a password'),
            'autocomplete': 'new-password',
        })
    )

    password2 = forms.CharField(
        label=_('Confirm Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Confirm your password'),
            'autocomplete': 'new-password',
        })
    )

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError(_('Name must be at least 2 characters long.'))
        return name

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise forms.ValidationError(_('Username is required.'))
        if not re.match(r'^[a-zA-Z0-9_]{4,20}$', username):
            raise forms.ValidationError(_('Username must be 4-20 characters and contain only letters, numbers, and underscore.'))

        if CustomUser.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(_('This username is already taken.'))

        # Block active pending registration collisions as well.
        if PendingRegistration.objects.filter(username__iexact=username, is_verified=False).exists():
            raise forms.ValidationError(_('This username is currently reserved. Please choose another one.'))

        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_('This email is already registered.'))
        if PendingRegistration.objects.filter(email__iexact=email, is_verified=False).exists():
            raise forms.ValidationError(_('A pending registration already exists for this email. Please verify OTP or try again later.'))
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError(_('Mobile number must be exactly 10 digits.'))
        if not phone.startswith(('6', '7', '8', '9')):
            raise forms.ValidationError(_('Mobile number must start with 6, 7, 8, or 9.'))
        if CustomUser.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError(_('This mobile number is already registered.'))
        return phone

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode', '').strip()
        if not pincode.isdigit() or len(pincode) != 6:
            raise forms.ValidationError(_('Pincode must be exactly 6 digits.'))
        return pincode

    def clean_aadhar_number(self):
        aadhar_number = self.cleaned_data.get('aadhar_number', '').strip()
        if not aadhar_number:
            return ''
        if not aadhar_number.isdigit() or len(aadhar_number) != 12:
            raise forms.ValidationError(_('Aadhaar number must be exactly 12 digits.'))
        if CustomUser.objects.filter(aadhar_number=aadhar_number).exists():
            raise forms.ValidationError(_('This Aadhaar number is already registered.'))
        return aadhar_number

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if not dob:
            return dob

        today = date.today()
        if dob >= today:
            raise forms.ValidationError(_('Date of birth must be in the past.'))

        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise forms.ValidationError(_('You must be at least 18 years old to self-register.'))
        return dob

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if not photo:
            return photo
        if photo.size > 2 * 1024 * 1024:
            raise forms.ValidationError(_('Profile photo must be less than 2MB.'))
        return photo

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')

        if password1:
            validate_password(password1)

        return cleaned_data

    def clean_password1(self):
        password = self.cleaned_data.get('password1', '')
        if len(password) < 8:
            raise forms.ValidationError(_('Password must be at least 8 characters long.'))
        return password

    def get_pending_payload(self):
        """Return normalized, validated payload for pending OTP registration."""
        name = self.cleaned_data['name'].strip()
        return {
            'name': name,
            'first_name': name.split()[0],
            'last_name': ' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
            'email': self.cleaned_data['email'].strip().lower(),
            'phone_number': self.cleaned_data['phone_number'].strip(),
            'gender': self.cleaned_data['gender'],
            'date_of_birth': self.cleaned_data['date_of_birth'],
            'address': self.cleaned_data['address'].strip(),
            'state': self.cleaned_data['state'].strip(),
            'district': self.cleaned_data['district'].strip(),
            'pincode': self.cleaned_data['pincode'].strip(),
            'aadhar_number': self.cleaned_data.get('aadhar_number', '').strip(),
            'profile_photo': self.cleaned_data.get('profile_photo'),
            'raw_password': self.cleaned_data['password1'],
            'username': self.cleaned_data['username'].strip(),
        }


class StaffCreationForm(UserCreationForm):
    """
    Staff creation form for admins only
    """

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address'
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

    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'phone_number', 'aadhar_number', 'date_of_birth',
            'address', 'village', 'pincode', 'password1', 'password2'
        ]

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if CustomUser.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("This phone number is already registered.")
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError("Phone number must be exactly 10 digits.")
        if not phone.startswith(('6', '7', '8', '9')):
            raise forms.ValidationError("Phone number must start with 6, 7, 8, or 9.")
        return phone

    def clean_aadhar_number(self):
        aadhar = self.cleaned_data.get('aadhar_number')
        if aadhar:
            if not aadhar.isdigit() or len(aadhar) != 12:
                raise forms.ValidationError("Aadhar number must be exactly 12 digits.")
            if CustomUser.objects.filter(aadhar_number=aadhar).exists():
                raise forms.ValidationError("This Aadhar number is already registered.")
        return aadhar

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if pincode:
            if not pincode.isdigit() or len(pincode) != 6:
                raise forms.ValidationError("Pincode must be exactly 6 digits.")
        return pincode

    def clean_username(self):
        import re
        username = self.cleaned_data.get('username')
        if not re.match(r'^[\w.@+-]+$', username):
            raise forms.ValidationError("Username can only contain letters, numbers, @, dot, plus, minus, and underscore.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'staff'
        user.is_active = True
        user.email_verified = True
        user.is_staff = True
        user.is_superuser = False
        if commit:
            user.save()
        return user


class UserSettingsForm(forms.ModelForm):
    """Profile settings form for citizen and staff users."""

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_photo']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit mobile number'}),
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise forms.ValidationError('Email is required.')

        qs = CustomUser.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError('Phone number must be exactly 10 digits.')

        qs = CustomUser.objects.filter(phone_number=phone)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('This phone number is already registered.')
        return phone


class AdminUserForm(forms.ModelForm):
    """Admin form for editing general users."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'role' in self.fields:
            self.fields['role'].choices = [
                ('citizen', 'Citizen'),
                ('staff', 'Panchayat Staff'),
            ]

    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone_number',
            'address', 'village', 'taluka', 'district', 'state', 'pincode',
            'profile_photo', 'role', 'is_active',
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'village': forms.TextInput(attrs={'class': 'form-control'}),
            'taluka': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if len(username) < 4 or len(username) > 20:
            raise forms.ValidationError('Username must be 4-20 characters long.')

        if not username.replace('_', '').replace('-', '').isalnum():
            raise forms.ValidationError('Username can only contain letters, numbers, and underscore.')

        existing = CustomUser.objects.filter(username=username)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise forms.ValidationError('This username is already taken.')

        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        existing = CustomUser.objects.filter(email__iexact=email)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise forms.ValidationError('This email is already registered.')

        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number', '').strip()
        existing = CustomUser.objects.filter(phone_number=phone_number)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise forms.ValidationError('This phone number is already registered.')

        return phone_number

    def clean_role(self):
        role = self.cleaned_data.get('role', 'citizen')
        if role not in ['citizen', 'staff']:
            raise forms.ValidationError('Invalid role selected.')

        return role

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data.get('role', user.role)
        user.is_active = self.cleaned_data.get('is_active', user.is_active)

        if user.role == 'staff':
            user.is_staff = True
            user.is_superuser = False
        elif user.role == 'citizen':
            user.is_staff = False
            user.is_superuser = False

        if commit:
            user.save()
        return user


class AccountDeleteForm(forms.Form):
    confirmation = forms.CharField(
        label='Type DELETE to confirm',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'DELETE'
        })
    )

    def clean_confirmation(self):
        confirmation = self.cleaned_data.get('confirmation', '').strip().upper()
        if confirmation != 'DELETE':
            raise forms.ValidationError('Please type DELETE to confirm account deletion.')
        return confirmation


class UserPasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter current password',
            'autocomplete': 'current-password'
        })
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password'
        })
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password'
        })
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user or not self.user.check_password(current_password):
            raise forms.ValidationError('Current password is incorrect.')
        return current_password

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        validate_password(password, self.user)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', 'New passwords do not match.')

        if password1 and cleaned_data.get('current_password') and password1 == cleaned_data.get('current_password'):
            self.add_error('new_password1', 'New password must be different from current password.')

        return cleaned_data


class ForgotPasswordRequestForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your registered email address',
            'autocomplete': 'email'
        })
    )


class PasswordResetForm(forms.Form):
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password'
        })
    )
    new_password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password'
        })
    )

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', 'Passwords do not match.')
        return cleaned_data


class UserLoginForm(AuthenticationForm):
    """
    Custom Login Form
    """
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Username or Email')
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Password')
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


class BillRequestForm(forms.ModelForm):
    """Form to submit bill-related service requests."""

    class Meta:
        model = BillRequest
        fields = [
            'request_type',
            'account_or_consumer_number',
            'subject',
            'details',
            'attachment',
        ]
        widgets = {
            'request_type': forms.Select(attrs={'class': 'form-select'}),
            'account_or_consumer_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Consumer / account / property number'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Request subject'
            }),
            'details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your bill-related request in detail'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }


# ============================================
# ELECTRICITY / WATER / PROPERTY TAX FORMS
# ============================================

class ElectricityBillLookupForm(forms.Form):
    consumer_number = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter consumer number'
        })
    )


class WaterBillLookupForm(forms.Form):
    connection_number = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter water connection number'
        })
    )


class PropertyTaxRecordForm(forms.ModelForm):
    class Meta:
        model = PropertyTaxRecord
        fields = [
            'property_number',
            'owner_name',
            'property_address',
            'property_type',
            'built_up_area_sqft',
            'tax_rate_per_sqft',
            'tax_year',
            'due_date',
        ]
        widgets = {
            'property_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Property/House number'}),
            'owner_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Owner full name'}),
            'property_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Property address'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'built_up_area_sqft': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Built-up area in sq ft'}),
            'tax_rate_per_sqft': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Rate per sq ft'}),
            'tax_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2025-26'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean_tax_year(self):
        tax_year = self.cleaned_data.get('tax_year', '').strip()
        if len(tax_year) != 7 or '-' not in tax_year:
            raise forms.ValidationError('Tax year must be in format YYYY-YY (e.g., 2025-26).')
        return tax_year


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
# ADMIN STAFF CREATION FORM
# ============================================

class StaffCreationForm(forms.ModelForm):
    """
    Admin-only form for creating Staff accounts
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter temporary password'
        }),
        required=True
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        required=True
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'phone_number', 'password', 'confirm_password'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username (4-20 characters, letters/numbers/_ only)'
        })
        self.fields['first_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'First name'
        })
        self.fields['last_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Last name'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Email address'
        })
        self.fields['phone_number'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '10-digit mobile number'
        })
    
    def clean_username(self):
        """Validate username with strict rules"""
        username = self.cleaned_data.get('username')
        
        # Length validation
        if len(username) < 4 or len(username) > 20:
            raise forms.ValidationError("Username must be 4-20 characters long.")
        
        # Character validation - only letters, numbers, and underscore
        if not username.replace('_', '').replace('-', '').isalnum():
            raise forms.ValidationError("Username can only contain letters, numbers, and underscore.")
        
        # No spaces
        if ' ' in username:
            raise forms.ValidationError("Username cannot contain spaces.")
        
        # Check uniqueness
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        
        return username
    
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
    
    def clean(self):
        """Validate password confirmation"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        if password and len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save staff user with staff role"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'staff'  # Force staff role
        user.is_staff = True  # Django staff permission
        user.is_superuser = False
        user.is_active = self.cleaned_data.get('is_active', True)
        if commit:
            user.save()
        return user


class StaffManagementForm(forms.ModelForm):
    """Edit form for existing staff accounts."""

    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone_number',
            'address', 'village', 'taluka', 'district', 'state', 'pincode',
            'profile_photo', 'is_active',
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'village': forms.TextInput(attrs={'class': 'form-control'}),
            'taluka': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if len(username) < 4 or len(username) > 20:
            raise forms.ValidationError('Username must be 4-20 characters long.')

        if not username.replace('_', '').replace('-', '').isalnum():
            raise forms.ValidationError('Username can only contain letters, numbers, and underscore.')

        existing = CustomUser.objects.filter(username=username)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise forms.ValidationError('This username is already taken.')

        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        existing = CustomUser.objects.filter(email__iexact=email)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise forms.ValidationError('This email is already registered.')

        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number', '').strip()
        existing = CustomUser.objects.filter(phone_number=phone_number)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise forms.ValidationError('This phone number is already registered.')

        return phone_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'staff'
        user.is_staff = True
        user.is_superuser = False
        if commit:
            user.save()
        return user


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

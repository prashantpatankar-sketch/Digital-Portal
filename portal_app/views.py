"""
Views for Digital Gram Panchayat Portal

Contains all view functions for:
- Authentication (Login, Registration, Logout)
- Citizen Dashboard
- Application Submissions
- Application Tracking
- Admin Dashboard
- Application Review
- PDF Generation
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO

from .models import (
    CustomUser, Application, BirthCertificate, DeathCertificate,
    IncomeCertificate, TaxPayment, Complaint, ApplicationStatusHistory,
    ComplaintHistory
)
from .forms import (
    CitizenRegistrationForm, UserLoginForm, BirthCertificateForm,
    DeathCertificateForm, IncomeCertificateForm, TaxPaymentForm,
    ComplaintForm, ApplicationReviewForm, ComplaintUpdateForm,
    OTPVerificationForm, ResendOTPForm
)
from .decorators import (
    role_required, admin_required, staff_required, 
    citizen_required, staff_or_admin_required
)


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_client_ip(request):
    """Best-effort client IP extraction for rate limiting."""
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')

def create_status_history(application, old_status, new_status, changed_by, remarks=None):
    """
    Helper function to create application status history
    """
    ApplicationStatusHistory.objects.create(
        application=application,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by,
        remarks=remarks
    )


def generate_certificate_number(application_type):
    """
    Generate unique certificate number
    Format: CERT{TYPE}{TIMESTAMP}
    """
    type_prefix = application_type[:4].upper()
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    return f"CERT{type_prefix}{timestamp}"


def get_application_statistics(user=None):
    """
    Get application statistics for dashboard
    """
    if user:
        applications = Application.objects.filter(applicant=user)
    else:
        applications = Application.objects.all()
    
    stats = {
        'total': applications.count(),
        'pending': applications.filter(status='pending').count(),
        'under_review': applications.filter(status='under_review').count(),
        'approved': applications.filter(status='approved').count(),
        'rejected': applications.filter(status='rejected').count(),
    }
    return stats


# ============================================
# PUBLIC VIEWS
# ============================================

def home(request):
    """
    Homepage - Public view
    """
    context = {
        'title': 'Home',
    }
    return render(request, 'portal_app/home.html', context)


def about(request):
    """
    About page
    """
    context = {
        'title': 'About Us',
    }
    return render(request, 'portal_app/about.html', context)


def services(request):
    """
    Services page listing all available services
    """
    context = {
        'title': 'Services',
    }
    return render(request, 'portal_app/services.html', context)


# ============================================
# AUTHENTICATION VIEWS
# ============================================

def register_view(request):
    """
    User Registration with OTP Email Verification
    
    Flow:
    1. User fills registration form
    2. Account created as inactive (is_active=False)
    3. OTP generated and sent to email
    4. User redirected to OTP verification page
    5. Account activated only after OTP verification
    
    Security:
    - Account inactive until email verified
    - OTP expires in 10 minutes
    - Maximum 3 verification attempts
    """
    if request.user.is_authenticated:
        # Redirect based on role if already logged in
        if request.user.role == 'admin':
            return redirect('admin_dashboard')
        elif request.user.role == 'staff':
            return redirect('admin_dashboard')
        else:
            return redirect('dashboard')
    
    if request.method == 'POST':
        form = CitizenRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            role = form.cleaned_data.get('role', 'citizen')
            user.role = role
            
            # IMPORTANT: Account is inactive until email verified
            user.is_active = False
            user.email_verified = False
            user.save()
            
            # Generate and send OTP
            from .security_utils import create_otp_for_user, send_otp_email
            
            try:
                otp = create_otp_for_user(user)
                
                if send_otp_email(user, otp.otp_code):
                    messages.success(
                        request,
                        f'Registration successful! A 6-digit OTP has been sent to {user.email}. '
                        'Please verify your email to activate your account.'
                    )
                    # Store user ID in session for OTP verification
                    request.session['pending_verification_user_id'] = user.id
                    return redirect('verify_otp')
                else:
                    messages.error(
                        request,
                        'Registration successful, but failed to send verification email. '
                        'Please contact support.'
                    )
                    return redirect('login')
            
            except Exception as e:
                messages.error(
                    request,
                    'An error occurred during registration. Please try again.'
                )
                # Delete the user if OTP generation failed
                user.delete()
                return redirect('register')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CitizenRegistrationForm()
    
    context = {
        'title': 'Register',
        'form': form,
    }
    return render(request, 'portal_app/register.html', context)


def login_view(request):
    """
    User Login with Email Verification Check
    
    Security:
    - Checks if email is verified before allowing login
    - Redirects to OTP verification if email not verified
    - Role-based authentication and redirection
    """
    if request.user.is_authenticated:
        # Redirect based on role if already logged in
        if request.user.role == 'admin':
            return redirect('admin_dashboard')
        elif request.user.role == 'staff':
            return redirect('admin_dashboard')
        else:
            return redirect('dashboard')
    
    if request.method == 'POST':
        from .security_utils import check_rate_limit, rate_limit_exceeded_response

        username_input = request.POST.get('username', '').strip()
        client_ip = get_client_ip(request)
        rate_limit_id = f"login:{username_input}:{client_ip}"
        if not check_rate_limit(rate_limit_id, limit=5, period=300):
            return rate_limit_exceeded_response()

        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            # Allow login with email address
            if user is None and '@' in username:
                matched_user = CustomUser.objects.filter(email__iexact=username).first()
                if matched_user:
                    user = authenticate(username=matched_user.username, password=password)
            
            if user is not None:
                # NEW: Check if email is verified
                if not user.email_verified:
                    messages.warning(
                        request,
                        'Your email is not verified. Please verify your email to login.'
                    )
                    # Store user ID for OTP verification
                    request.session['pending_verification_user_id'] = user.id
                    
                    # Resend OTP
                    from .security_utils import resend_otp
                    success, resend_msg = resend_otp(user)
                    if success:
                        messages.info(request, resend_msg)
                    else:
                        messages.error(request, resend_msg)
                    
                    return redirect('verify_otp')
                
                # Check if account is active (for staff/admin approval)
                if not user.is_active:
                    messages.error(
                        request,
                        'Your account is pending approval. Please contact the administrator.'
                    )
                    return redirect('login')
                
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                
                # Role-based redirection
                if user.role == 'admin':
                    return redirect('admin_dashboard')
                elif user.role == 'staff':
                    return redirect('admin_dashboard')  # Staff dashboard
                else:
                    return redirect('dashboard')  # Citizen dashboard
            else:
                messages.error(request, 'Invalid username/email or password.')
        else:
            messages.error(request, 'Invalid username/email or password.')
    else:
        form = UserLoginForm()
    
    context = {
        'title': 'Login',
        'form': form,
    }
    return render(request, 'portal_app/login.html', context)


@login_required
def logout_view(request):
    """
    User Logout - Secure logout with session cleanup
    """
    user_name = request.user.first_name or request.user.username
    logout(request)
    messages.info(request, f'Goodbye {user_name}! You have been logged out successfully.')
    return redirect('home')


# ============================================
# CITIZEN DASHBOARD
# ============================================

@login_required
def dashboard(request):
    """
    Citizen Dashboard - Shows overview of applications and services
    """
    if request.user.role in ['staff', 'admin']:
        return redirect('admin_dashboard')
    
    # Get user's applications
    applications = Application.objects.filter(applicant=request.user)
    
    # Statistics
    stats = {
        'total_applications': applications.count(),
        'pending': applications.filter(status='pending').count(),
        'approved': applications.filter(status='approved').count(),
        'rejected': applications.filter(status='rejected').count(),
    }
    
    # Recent applications
    recent_applications = applications[:5]
    
    # Get user's complaints
    complaints = Complaint.objects.filter(complainant=request.user)[:5]
    
    context = {
        'title': 'Dashboard',
        'stats': stats,
        'recent_applications': recent_applications,
        'complaints': complaints,
    }
    return render(request, 'portal_app/citizen/dashboard.html', context)


# ============================================
# BIRTH CERTIFICATE VIEWS
# ============================================

@citizen_required
def apply_birth_certificate(request):
    """
    Apply for Birth Certificate with document upload
    """
    if request.method == 'POST':
        form = BirthCertificateForm(request.POST, request.FILES)
        if form.is_valid():
            # Create Application first
            application = Application.objects.create(
                applicant=request.user,
                application_type='birth_certificate',
                status='pending'
            )
            
            # Create Birth Certificate linked to Application
            birth_cert = form.save(commit=False)
            birth_cert.application = application
            birth_cert.save()
            
            # Create initial status history
            create_status_history(
                application=application,
                old_status='',
                new_status='pending',
                changed_by=request.user,
                remarks='Application submitted'
            )
            
            messages.success(
                request,
                f'Birth certificate application submitted successfully! '
                f'Application Number: <strong>{application.application_number}</strong>. '
                f'You will be notified once it is reviewed.'
            )
            return redirect('application_detail', application_id=application.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BirthCertificateForm()
    
    context = {
        'title': 'Apply for Birth Certificate',
        'form': form,
        'application_type': 'birth_certificate',
    }
    return render(request, 'portal_app/citizen/apply_birth_certificate.html', context)


# ============================================
# DEATH CERTIFICATE VIEWS
# ============================================

@citizen_required
def apply_death_certificate(request):
    """
    Apply for Death Certificate with document upload
    """
    if request.method == 'POST':
        form = DeathCertificateForm(request.POST, request.FILES)
        if form.is_valid():
            # Create Application first
            application = Application.objects.create(
                applicant=request.user,
                application_type='death_certificate',
                status='pending'
            )
            
            # Create Death Certificate linked to Application
            death_cert = form.save(commit=False)
            death_cert.application = application
            death_cert.save()
            
            # Create initial status history
            create_status_history(
                application=application,
                old_status='',
                new_status='pending',
                changed_by=request.user,
                remarks='Application submitted'
            )
            
            messages.success(
                request,
                f'Death certificate application submitted successfully! '
                f'Application Number: <strong>{application.application_number}</strong>. '
                f'You will be notified once it is reviewed.'
            )
            return redirect('application_detail', application_id=application.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DeathCertificateForm()
    
    context = {
        'title': 'Apply for Death Certificate',
        'form': form,
        'application_type': 'death_certificate',
    }
    return render(request, 'portal_app/citizen/apply_death_certificate.html', context)


# ============================================
# INCOME CERTIFICATE VIEWS
# ============================================

@citizen_required
def apply_income_certificate(request):
    """
    Apply for Income Certificate with document upload
    """
    if request.method == 'POST':
        form = IncomeCertificateForm(request.POST, request.FILES)
        if form.is_valid():
            # Create Application first
            application = Application.objects.create(
                applicant=request.user,
                application_type='income_certificate',
                status='pending'
            )
            
            # Create Income Certificate linked to Application
            income_cert = form.save(commit=False)
            income_cert.application = application
            income_cert.save()
            
            # Create initial status history
            create_status_history(
                application=application,
                old_status='',
                new_status='pending',
                changed_by=request.user,
                remarks='Application submitted'
            )
            
            messages.success(
                request,
                f'Income certificate application submitted successfully! '
                f'Application Number: <strong>{application.application_number}</strong>. '
                f'You will be notified once it is reviewed.'
            )
            return redirect('application_detail', application_id=application.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = IncomeCertificateForm()
    
    context = {
        'title': 'Apply for Income Certificate',
        'form': form,
        'application_type': 'income_certificate',
    }
    return render(request, 'portal_app/citizen/apply_income_certificate.html', context)


# ============================================
# TAX PAYMENT VIEWS
# ============================================

@login_required
@citizen_required
def pay_tax(request):
    """
    Tax Payment Form
    Citizen only - access controlled by decorator
    """
    if request.method == 'POST':
        form = TaxPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            # Create Application first
            tax_type = form.cleaned_data['tax_type']
            application = Application.objects.create(
                applicant=request.user,
                application_type=tax_type,
                status='pending'
            )
            
            # Create Tax Payment linked to Application
            tax_payment = form.save(commit=False)
            tax_payment.application = application
            tax_payment.save()
            
            # Create initial status history
            create_status_history(
                application=application,
                old_status='',
                new_status='pending',
                changed_by=request.user,
                remarks=f'{tax_type.replace("_", " ").title()} payment application submitted'
            )
            
            messages.success(
                request,
                f'<strong>Tax payment application submitted successfully!</strong><br>'
                f'Application Number: <strong>{application.application_number}</strong><br>'
                f'You can track your application status anytime.',
                extra_tags='safe'
            )
            return redirect('application_detail', application_id=application.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TaxPaymentForm()
    
    context = {
        'title': 'Pay Tax',
        'form': form,
    }
    return render(request, 'portal_app/citizen/pay_tax.html', context)


# ============================================
# COMPLAINT VIEWS
# ============================================

@login_required
def file_complaint(request):
    """
    File a Complaint/Grievance with automatic history tracking
    """
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.complainant = request.user
            complaint.save()
            
            # Create complaint history
            ComplaintHistory.objects.create(
                complaint=complaint,
                action='created',
                new_value=complaint.get_status_display(),
                performed_by=request.user,
                notes=f'Complaint filed: {complaint.subject}'
            )
            
            messages.success(
                request,
                f'<strong>Complaint filed successfully!</strong><br>'
                f'Complaint Number: <strong>{complaint.complaint_number}</strong><br>'
                f'We will review and assign it to the appropriate department.',
                extra_tags='safe'
            )
            return redirect('complaint_detail', complaint_id=complaint.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ComplaintForm()
    
    context = {
        'title': 'File Complaint',
        'form': form,
    }
    return render(request, 'portal_app/citizen/file_complaint.html', context)


@login_required
def my_complaints(request):
    """
    View user's complaints with filtering
    """
    complaints = Complaint.objects.filter(complainant=request.user).order_by('-filed_date')
    
    # Status filter
    status_filter = request.GET.get('status')
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    
    # Statistics
    total_complaints = Complaint.objects.filter(complainant=request.user).count()
    open_complaints = Complaint.objects.filter(complainant=request.user, status='open').count()
    resolved_complaints = Complaint.objects.filter(complainant=request.user, status='resolved').count()
    
    # Pagination
    paginator = Paginator(complaints, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'My Complaints',
        'page_obj': page_obj,
        'total_complaints': total_complaints,
        'open_complaints': open_complaints,
        'resolved_complaints': resolved_complaints,
        'status_filter': status_filter,
    }
    return render(request, 'portal_app/citizen/my_complaints.html', context)


@login_required
def complaint_detail(request, complaint_id):
    """
    View complaint details with complete history
    """
    complaint = get_object_or_404(Complaint, pk=complaint_id, complainant=request.user)
    
    # Get complaint history
    history = complaint.history.all().order_by('-performed_at')
    
    context = {
        'title': 'Complaint Details',
        'complaint': complaint,
        'history': history,
    }
    return render(request, 'portal_app/citizen/complaint_detail.html', context)


# ============================================
# APPLICATION TRACKING
# ============================================

@login_required
def my_applications(request):
    """
    View all applications submitted by user
    """
    applications = Application.objects.filter(applicant=request.user).order_by('-applied_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'My Applications',
        'page_obj': page_obj,
        'status_filter': status_filter,
    }
    return render(request, 'portal_app/citizen/my_applications.html', context)


@login_required
def application_detail(request, application_id):
    """
    View application details
    """
    application = get_object_or_404(Application, pk=application_id, applicant=request.user)
    
    # Get specific certificate details
    certificate_data = None
    if application.application_type == 'birth_certificate':
        certificate_data = application.birth_certificate
    elif application.application_type == 'death_certificate':
        certificate_data = application.death_certificate
    elif application.application_type == 'income_certificate':
        certificate_data = application.income_certificate
    elif application.application_type in ['water_tax', 'house_tax']:
        certificate_data = application.tax_payment
    
    # Get status history
    status_history = application.status_history.all()
    
    context = {
        'title': 'Application Details',
        'application': application,
        'certificate_data': certificate_data,
        'status_history': status_history,
    }
    return render(request, 'portal_app/citizen/application_detail.html', context)


# ============================================
# TRACK APPLICATION (Public with Application Number)
# ============================================

def track_application(request):
    """
    Public application tracking by application number
    """
    application = None
    application_number = request.GET.get('app_number', '').strip()
    
    if application_number:
        try:
            application = Application.objects.get(application_number=application_number)
        except Application.DoesNotExist:
            messages.error(request, 'Application not found. Please check the application number.')
    
    context = {
        'title': 'Track Application',
        'application': application,
        'application_number': application_number,
    }
    return render(request, 'portal_app/track_application.html', context)


# ============================================
# ADMIN DASHBOARD
# ============================================

@staff_or_admin_required
def admin_dashboard(request):
    """
    Government-Style Admin Dashboard with comprehensive statistics
    Staff and Admin only - access controlled by decorator
    """
    from datetime import timedelta
    from django.db.models import Count, Q
    
    # User Statistics
    total_citizens = CustomUser.objects.filter(role='citizen').count()
    total_staff = CustomUser.objects.filter(role='staff').count()
    total_admins = CustomUser.objects.filter(role='admin').count()
    inactive_users = CustomUser.objects.filter(is_active=False).count()
    new_users_today = CustomUser.objects.filter(
        date_joined__date=timezone.now().date()
    ).count()
    
    # Application Statistics
    total_applications = Application.objects.count()
    pending_applications = Application.objects.filter(status='pending').count()
    under_review_applications = Application.objects.filter(status='under_review').count()
    approved_applications = Application.objects.filter(status='approved').count()
    rejected_applications = Application.objects.filter(status='rejected').count()
    
    # Today's Statistics
    today = timezone.now().date()
    applications_today = Application.objects.filter(applied_date__date=today).count()
    approved_today = Application.objects.filter(
        status='approved',
        reviewed_date__date=today
    ).count()
    
    # This Week Statistics
    week_ago = timezone.now() - timedelta(days=7)
    applications_this_week = Application.objects.filter(
        applied_date__gte=week_ago
    ).count()
    
    # Application Type Breakdown
    app_type_stats = Application.objects.values('application_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Complaint Statistics
    total_complaints = Complaint.objects.count()
    open_complaints = Complaint.objects.filter(status='open').count()
    in_progress_complaints = Complaint.objects.filter(status='in_progress').count()
    resolved_complaints = Complaint.objects.filter(status='resolved').count()
    complaints_today = Complaint.objects.filter(filed_date__date=today).count()
    
    # Tax Payment Statistics
    total_tax_payments = TaxPayment.objects.count()
    water_tax_count = TaxPayment.objects.filter(tax_type='water_tax').count()
    house_tax_count = TaxPayment.objects.filter(tax_type='house_tax').count()
    
    # Certificate Statistics
    birth_certs = BirthCertificate.objects.filter(
        certificate_number__isnull=False
    ).count()
    death_certs = DeathCertificate.objects.filter(
        certificate_number__isnull=False
    ).count()
    income_certs = IncomeCertificate.objects.filter(
        certificate_number__isnull=False
    ).count()
    
    # Recent Activity
    recent_applications = Application.objects.select_related(
        'applicant'
    ).order_by('-applied_date')[:10]
    
    pending_applications_list = Application.objects.select_related(
        'applicant'
    ).filter(status='pending').order_by('-applied_date')[:10]
    
    recent_complaints = Complaint.objects.select_related(
        'complainant'
    ).order_by('-filed_date')[:5]
    
    # Staff pending approval
    pending_staff = CustomUser.objects.filter(
        role__in=['staff', 'admin'],
        is_active=False
    ).order_by('-date_joined')[:5]
    
    # Recent citizens
    recent_citizens = CustomUser.objects.filter(
        role='citizen',
        is_active=True
    ).order_by('-date_joined')[:10]
    
    # Status Distribution for Chart
    status_distribution = {
        'pending': pending_applications,
        'under_review': under_review_applications,
        'approved': approved_applications,
        'rejected': rejected_applications
    }
    
    context = {
        'title': 'Admin Dashboard',
        # User Stats
        'total_citizens': total_citizens,
        'total_staff': total_staff,
        'total_admins': total_admins,
        'inactive_users': inactive_users,
        'new_users_today': new_users_today,
        # Application Stats
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'under_review_applications': under_review_applications,
        'approved_applications': approved_applications,
        'rejected_applications': rejected_applications,
        'applications_today': applications_today,
        'approved_today': approved_today,
        'applications_this_week': applications_this_week,
        # Complaint Stats
        'total_complaints': total_complaints,
        'open_complaints': open_complaints,
        'in_progress_complaints': in_progress_complaints,
        'resolved_complaints': resolved_complaints,
        'complaints_today': complaints_today,
        # Certificate Stats
        'birth_certs': birth_certs,
        'death_certs': death_certs,
        'income_certs': income_certs,
        # Tax Stats
        'total_tax_payments': total_tax_payments,
        'water_tax_count': water_tax_count,
        'house_tax_count': house_tax_count,
        # Lists
        'recent_applications': recent_applications,
        'pending_applications_list': pending_applications_list,
        'recent_complaints': recent_complaints,
        'pending_staff': pending_staff,
        'recent_citizens': recent_citizens,
        'app_type_stats': app_type_stats,
        'status_distribution': status_distribution,
    }
    return render(request, 'portal_app/admin/dashboard.html', context)


# ============================================
# ADMIN APPLICATION MANAGEMENT
# ============================================

@staff_or_admin_required
def admin_applications(request):
    """
    View and manage all applications
    Staff and Admin only - access controlled by decorator
    """
    applications = Application.objects.all().order_by('-applied_date')
    
    # Filters
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    
    if status_filter:
        applications = applications.filter(status=status_filter)
    if type_filter:
        applications = applications.filter(application_type=type_filter)
    
    # Pagination
    paginator = Paginator(applications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Manage Applications',
        'page_obj': page_obj,
        'status_filter': status_filter,
        'type_filter': type_filter,
    }
    return render(request, 'portal_app/admin/applications.html', context)


@staff_or_admin_required
def admin_review_application(request, application_id):
    """
    Review and approve/reject application with status tracking
    Staff and Admin only - access controlled by decorator
    """
    application = get_object_or_404(Application, pk=application_id)
    
    # Get specific certificate details
    certificate_data = None
    if application.application_type == 'birth_certificate':
        certificate_data = application.birth_certificate
    elif application.application_type == 'death_certificate':
        certificate_data = application.death_certificate
    elif application.application_type == 'income_certificate':
        certificate_data = application.income_certificate
    elif application.application_type in ['water_tax', 'house_tax']:
        certificate_data = application.tax_payment
    
    if request.method == 'POST':
        form = ApplicationReviewForm(request.POST, instance=application)
        if form.is_valid():
            old_status = application.status
            updated_app = form.save(commit=False)
            updated_app.reviewed_by = request.user
            updated_app.reviewed_date = timezone.now()
            
            # If status changed, create history
            if old_status != updated_app.status:
                # Save application first
                updated_app.save()
                
                # Create status history
                create_status_history(
                    application=updated_app,
                    old_status=old_status,
                    new_status=updated_app.status,
                    changed_by=request.user,
                    remarks=updated_app.admin_remarks
                )
                
                # If approved, generate certificate number
                if updated_app.status == 'approved' and certificate_data:
                    if hasattr(certificate_data, 'certificate_number'):
                        if not certificate_data.certificate_number:
                            certificate_data.certificate_number = generate_certificate_number(
                                application.application_type
                            )
                            certificate_data.issued_date = timezone.now().date()
                            
                            # Set validity for income certificate (1 year)
                            if hasattr(certificate_data, 'valid_until'):
                                from datetime import timedelta
                                certificate_data.valid_until = timezone.now().date() + timedelta(days=365)
                            
                            certificate_data.save()
                
                status_msg = 'approved' if updated_app.status == 'approved' else updated_app.status
                messages.success(
                    request, 
                    f'Application {updated_app.application_number} has been {status_msg}!'
                )
            else:
                updated_app.save()
                messages.success(request, f'Application {updated_app.application_number} updated successfully!')
            
            return redirect('admin_applications')
    else:
        form = ApplicationReviewForm(instance=application)
    
    # Get status history
    status_history = application.status_history.all().order_by('-changed_at')
    
    context = {
        'title': 'Review Application',
        'application': application,
        'certificate_data': certificate_data,
        'form': form,
        'status_history': status_history,
    }
    return render(request, 'portal_app/admin/review_application.html', context)


# ============================================
# ADMIN COMPLAINT MANAGEMENT
# ============================================

@staff_or_admin_required
def admin_complaints(request):
    """
    View and manage all complaints with comprehensive filtering
    Staff and Admin only - access controlled by decorator
    """
    complaints = Complaint.objects.select_related('complainant', 'assigned_to').all().order_by('-filed_date')
    
    # Filters
    status_filter = request.GET.get('status')
    category_filter = request.GET.get('category')
    priority_filter = request.GET.get('priority')
    assigned_filter = request.GET.get('assigned')
    
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    if category_filter:
        complaints = complaints.filter(category=category_filter)
    if priority_filter:
        complaints = complaints.filter(priority=priority_filter)
    if assigned_filter == 'me':
        complaints = complaints.filter(assigned_to=request.user)
    elif assigned_filter == 'unassigned':
        complaints = complaints.filter(assigned_to__isnull=True)
    
    # Statistics
    total_complaints = Complaint.objects.count()
    open_complaints = Complaint.objects.filter(status='open').count()
    in_progress_complaints = Complaint.objects.filter(status='in_progress').count()
    resolved_complaints = Complaint.objects.filter(status='resolved').count()
    unassigned_complaints = Complaint.objects.filter(assigned_to__isnull=True).count()
    urgent_complaints = Complaint.objects.filter(priority='urgent', status__in=['open', 'in_progress']).count()
    
    # Pagination
    paginator = Paginator(complaints, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Manage Complaints',
        'page_obj': page_obj,
        'total_complaints': total_complaints,
        'open_complaints': open_complaints,
        'in_progress_complaints': in_progress_complaints,
        'resolved_complaints': resolved_complaints,
        'unassigned_complaints': unassigned_complaints,
        'urgent_complaints': urgent_complaints,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'priority_filter': priority_filter,
        'assigned_filter': assigned_filter,
    }
    return render(request, 'portal_app/admin/complaints.html', context)


@staff_or_admin_required
def admin_update_complaint(request, complaint_id):
    """
    Update complaint status, assignment, and resolution with history tracking
    Staff and Admin only - access controlled by decorator
    """
    complaint = get_object_or_404(Complaint, pk=complaint_id)
    old_status = complaint.status
    old_priority = complaint.priority
    old_assigned_to = complaint.assigned_to
    
    if request.method == 'POST':
        form = ComplaintUpdateForm(request.POST, instance=complaint)
        if form.is_valid():
            updated_complaint = form.save(commit=False)
            
            # Track status change
            if old_status != updated_complaint.status:
                ComplaintHistory.objects.create(
                    complaint=complaint,
                    action='status_changed',
                    old_value=old_status,
                    new_value=updated_complaint.status,
                    performed_by=request.user,
                    notes=f'Status changed from {complaint.get_status_display()} to {updated_complaint.get_status_display()}'
                )
                
                # Set resolved date
                if updated_complaint.status == 'resolved' and not complaint.resolved_date:
                    updated_complaint.resolved_date = timezone.now()
                    ComplaintHistory.objects.create(
                        complaint=complaint,
                        action='resolved',
                        performed_by=request.user,
                        notes=updated_complaint.resolution_remarks or 'Complaint resolved'
                    )
            
            # Track priority change
            if old_priority != updated_complaint.priority:
                ComplaintHistory.objects.create(
                    complaint=complaint,
                    action='priority_changed',
                    old_value=old_priority,
                    new_value=updated_complaint.priority,
                    performed_by=request.user
                )
            
            # Track assignment change
            if old_assigned_to != updated_complaint.assigned_to:
                ComplaintHistory.objects.create(
                    complaint=complaint,
                    action='assigned',
                    old_value=str(old_assigned_to) if old_assigned_to else 'Unassigned',
                    new_value=str(updated_complaint.assigned_to) if updated_complaint.assigned_to else 'Unassigned',
                    performed_by=request.user,
                    notes=f'Assigned to {updated_complaint.assigned_to.get_full_name()}' if updated_complaint.assigned_to else 'Assignment removed'
                )
            
            updated_complaint.save()
            
            messages.success(
                request,
                f'<strong>Complaint {complaint.complaint_number} updated!</strong><br>'
                f'Status: {updated_complaint.get_status_display()}',
                extra_tags='safe'
            )
            return redirect('admin_complaints')
    else:
        form = ComplaintUpdateForm(instance=complaint)
    
    # Get complaint history
    history = complaint.history.all().order_by('-performed_at')
    
    context = {
        'title': 'Update Complaint',
        'complaint': complaint,
        'form': form,
        'history': history,
    }
    return render(request, 'portal_app/admin/update_complaint.html', context)


# ============================================
# PDF GENERATION (Download Certificate)
# ============================================

@login_required
def download_certificate(request, application_id):
    """
    Generate and download PDF certificate
    """
    application = get_object_or_404(Application, pk=application_id)
    
    # Check if user has permission
    if not (
        request.user == application.applicant
        or request.user.role in ['staff', 'admin']
        or request.user.is_staff
    ):
        raise Http404("Certificate not found")
    
    # Only approved applications can be downloaded
    if application.status != 'approved':
        messages.error(request, 'Certificate not yet approved.')
        return redirect('application_detail', application_id=application_id)
    
    # Generate PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#283593'),
        spaceAfter=12,
    )
    
    # Header
    elements.append(Paragraph("Government of India", title_style))
    elements.append(Paragraph("Digital Gram Panchayat Portal", styles['Heading2']))
    elements.append(Spacer(1, 0.5*inch))
    
    # Get certificate specific data
    if application.application_type == 'birth_certificate':
        cert = application.birth_certificate
        elements.append(Paragraph("BIRTH CERTIFICATE", title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        data = [
            ['Certificate Number:', cert.certificate_number or 'N/A'],
            ['Issued Date:', str(cert.issued_date) if cert.issued_date else 'N/A'],
            ['', ''],
            ['Child Name:', cert.child_name],
            ['Date of Birth:', str(cert.date_of_birth)],
            ['Gender:', cert.get_child_gender_display()],
            ['Place of Birth:', cert.place_of_birth],
            ['Father Name:', cert.father_name],
            ['Mother Name:', cert.mother_name],
            ['Permanent Address:', cert.permanent_address],
        ]
    
    elif application.application_type == 'death_certificate':
        cert = application.death_certificate
        elements.append(Paragraph("DEATH CERTIFICATE", title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        data = [
            ['Certificate Number:', cert.certificate_number or 'N/A'],
            ['Issued Date:', str(cert.issued_date) if cert.issued_date else 'N/A'],
            ['', ''],
            ['Deceased Name:', cert.deceased_name],
            ['Date of Death:', str(cert.date_of_death)],
            ['Age:', str(cert.deceased_age)],
            ['Gender:', cert.get_deceased_gender_display()],
            ['Place of Death:', cert.place_of_death],
            ['Cause of Death:', cert.cause_of_death],
            ['Permanent Address:', cert.permanent_address],
        ]
    
    elif application.application_type == 'income_certificate':
        cert = application.income_certificate
        elements.append(Paragraph("INCOME CERTIFICATE", title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        data = [
            ['Certificate Number:', cert.certificate_number or 'N/A'],
            ['Issued Date:', str(cert.issued_date) if cert.issued_date else 'N/A'],
            ['Valid Until:', str(cert.valid_until) if cert.valid_until else 'N/A'],
            ['', ''],
            ['Applicant Name:', cert.applicant_name],
            ['Father/Husband Name:', cert.father_husband_name],
            ['Occupation:', cert.occupation],
            ['Annual Income:', f'₹{cert.annual_income}'],
            ['Income Source:', cert.get_income_source_display()],
            ['Purpose:', cert.purpose_of_certificate],
            ['Residential Address:', cert.residential_address],
        ]
    
    else:
        # Tax payment or other
        elements.append(Paragraph("CERTIFICATE", title_style))
        data = [
            ['Application Number:', application.application_number],
            ['Type:', application.get_application_type_display()],
            ['Status:', application.get_status_display()],
        ]
    
    # Create table
    table = Table(data, colWidths=[2.5*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Footer
    elements.append(Paragraph("This is a computer-generated certificate.", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(f"Generated on: {timezone.now().strftime('%B %d, %Y')}", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    # Return PDF response
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_{application.application_number}.pdf"'
    
    return response


# ============================================
# OTP EMAIL VERIFICATION VIEWS
# ============================================

def verify_otp_view(request):
    """
    OTP Verification View
    
    Flow:
    1. User receives OTP via email after registration
    2. User enters 6-digit OTP
    3. OTP validated (expiration, attempts, correctness)
    4. Account activated on successful verification
    
    Security:
    - OTP expires in 10 minutes
    - Maximum 3 verification attempts per OTP
    - One-time use only
    - Rate limiting on resend (1 per minute)
    """
    # Get user ID from session
    user_id = request.session.get('pending_verification_user_id')
    
    if not user_id:
        messages.error(request, 'No pending verification found. Please register again.')
        return redirect('register')
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid verification session. Please register again.')
        return redirect('register')
    
    # Check if already verified
    if user.email_verified:
        messages.info(request, 'Your email is already verified. Please login.')
        # Clear session
        if 'pending_verification_user_id' in request.session:
            del request.session['pending_verification_user_id']
        return redirect('login')
    
    # Get latest OTP for user
    from .models import EmailOTP
    latest_otp = EmailOTP.objects.filter(
        user=user,
        is_used=False
    ).order_by('-created_at').first()
    
    if request.method == 'POST':
        from .security_utils import check_rate_limit, rate_limit_exceeded_response
        client_ip = get_client_ip(request)
        rate_limit_id = f"otp_verify:{user.id}:{client_ip}"
        if not check_rate_limit(rate_limit_id, limit=10, period=600):
            return rate_limit_exceeded_response()

        form = OTPVerificationForm(request.POST)
        
        if form.is_valid():
            otp_code = form.cleaned_data.get('otp_code')
            
            # Verify OTP
            from .security_utils import verify_otp
            success, message = verify_otp(user, otp_code)
            
            if success:
                messages.success(request, message)
                # Clear session
                if 'pending_verification_user_id' in request.session:
                    del request.session['pending_verification_user_id']
                return redirect('login')
            else:
                messages.error(request, message)
        else:
            messages.error(request, 'Please enter a valid 6-digit OTP.')
    else:
        form = OTPVerificationForm()
    
    # Calculate time remaining
    time_remaining = 0
    attempts_left = 3
    minutes = 0
    seconds = 0
    
    if latest_otp and latest_otp.is_valid():
        time_remaining = latest_otp.get_time_remaining()
        attempts_left = 3 - latest_otp.verification_attempts
        # Calculate minutes and seconds
        minutes = time_remaining // 60
        seconds = time_remaining % 60
    
    context = {
        'title': 'Verify Email',
        'form': form,
        'user': user,
        'email': user.email,
        'time_remaining': time_remaining,
        'minutes': minutes,
        'seconds': seconds,
        'attempts_left': attempts_left,
        'otp_exists': latest_otp is not None,
    }
    
    return render(request, 'portal_app/verify_otp.html', context)


def resend_otp_view(request):
    """
    Resend OTP View
    
    Security:
    - Rate limiting: 1 OTP per minute
    - Invalidates previous OTPs
    - CSRF protection via POST method
    """
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('verify_otp')
    
    # Get user ID from session
    user_id = request.session.get('pending_verification_user_id')
    
    if not user_id:
        messages.error(request, 'No pending verification found.')
        return redirect('register')
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid verification session.')
        return redirect('register')
    
    from .security_utils import check_rate_limit, rate_limit_exceeded_response
    client_ip = get_client_ip(request)
    rate_limit_id = f"otp_resend:{user.id}:{client_ip}"
    if not check_rate_limit(rate_limit_id, limit=3, period=600):
        return rate_limit_exceeded_response()

    # Resend OTP
    from .security_utils import resend_otp
    success, message = resend_otp(user)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return redirect('verify_otp')

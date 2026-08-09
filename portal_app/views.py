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
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from django.http import HttpResponse, Http404, JsonResponse
from django.http import FileResponse
from django.core.paginator import Paginator
from django.core.files.base import ContentFile
from django.contrib.sessions.models import Session
from django.conf import settings
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext as _
from datetime import datetime, timedelta
import json
import csv
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
import base64
import binascii
import uuid
from django.template.loader import render_to_string
from .email_utils import send_official_email, PORTAL_LOGO_DATA_URI

from .models import (
    CustomUser, Application, BirthCertificate, DeathCertificate,
    IncomeCertificate, TaxPayment, Complaint, ApplicationStatusHistory,
    ComplaintHistory, ElectricityBill, WaterBill, PropertyTaxRecord,
    BillRequest, Notification, UserActivity, EmailOTP, PendingRegistration
)
from .forms import (
    CitizenRegistrationForm, UserLoginForm, BirthCertificateForm,
    DeathCertificateForm, IncomeCertificateForm, TaxPaymentForm,
    ComplaintForm, ApplicationReviewForm, ComplaintUpdateForm,
    OTPVerificationForm, ResendOTPForm, StaffCreationForm, StaffManagementForm,
    ElectricityBillLookupForm, WaterBillLookupForm, PropertyTaxRecordForm,
    BillRequestForm, UserSettingsForm, AccountDeleteForm,
    ForgotPasswordRequestForm, PasswordResetForm, UserPasswordChangeForm,
    AdminUserForm
)
from .decorators import (
    role_required, admin_required, staff_required, 
    citizen_required, staff_or_admin_required
)
from .utils import number_to_marathi_words, get_marathi_date, format_marathi_address
from .chatbot_service import build_chatbot_response
from .admin_analytics import (
    collect_admin_analytics,
    send_admin_report_email,
    CERTIFICATE_TYPES,
    BILL_TYPES,
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


def _redirect_authenticated_user(user):
    """Send users to the dashboard that matches their portal privileges."""
    role = getattr(user, 'role', '')
    if user.is_superuser or role == 'admin':
        return redirect('admin_dashboard')
    if user.is_staff or role == 'staff':
        return redirect('staff_dashboard')
    return redirect('dashboard')


def _force_logout_user_ids(user_ids):
    """Remove active sessions for the given user IDs."""
    if not user_ids:
        return 0

    deleted_sessions = 0
    for session in Session.objects.all().iterator():
        try:
            data = session.get_decoded()
        except Exception:
            continue

        auth_user_id = data.get('_auth_user_id')
        if auth_user_id and str(auth_user_id) in {str(user_id) for user_id in user_ids}:
            session.delete()
            deleted_sessions += 1

    return deleted_sessions


def _sync_staff_user(user, *, is_active=None):
    """Keep staff users aligned with the portal's staff account rules."""
    user.role = 'staff'
    user.is_staff = True
    user.is_superuser = False
    if is_active is not None:
        user.is_active = is_active
    return user

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


def create_notification(recipient, title, message, category='system', target_url=''):
    """Create in-app notification for a user."""
    if not recipient:
        return None
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        category=category,
        target_url=target_url or ''
    )


def _normalize_otp_code(otp_code):
    """Return a compact digit-only OTP string."""
    return ''.join(ch for ch in str(otp_code or '').strip() if ch.isdigit())


def _store_pending_registration_session(request, pending_registration):
    """Persist the pending registration identity in session for OTP verification."""
    request.session['pending_registration_id'] = pending_registration.id
    request.session['pending_registration_email'] = pending_registration.email
    request.session['pending_registration_username'] = pending_registration.username
    request.session['pending_registration_phone_number'] = pending_registration.phone_number
    request.session.modified = True


def _store_pending_registration_otp_session(request, otp_code):
    """Persist the current registration OTP in session for reliable verification."""
    request.session['pending_registration_otp'] = str(otp_code or '').strip()
    request.session.modified = True


def _clear_pending_registration_session(request):
    """Remove all pending registration session markers."""
    for key in [
        'pending_registration_id',
        'pending_registration_email',
        'pending_registration_username',
        'pending_registration_phone_number',
        'pending_registration_otp',
    ]:
        request.session.pop(key, None)
    request.session.modified = True


def _get_pending_registration_from_session(request):
    """Resolve the active pending registration even if the primary session key is stale."""
    pending_id = request.session.get('pending_registration_id')
    pending = None

    if pending_id:
        pending = PendingRegistration.objects.filter(id=pending_id, is_verified=False).first()

    if pending:
        return pending

    lookup = Q()
    email = request.session.get('pending_registration_email', '').strip().lower()
    username = request.session.get('pending_registration_username', '').strip()
    phone_number = request.session.get('pending_registration_phone_number', '').strip()

    if email:
        lookup |= Q(email__iexact=email)
    if username:
        lookup |= Q(username__iexact=username)
    if phone_number:
        lookup |= Q(phone_number=phone_number)

    if not lookup:
        _clear_pending_registration_session(request)
        return None

    pending = PendingRegistration.objects.filter(lookup, is_verified=False).order_by('-created_at').first()
    if pending:
        _store_pending_registration_session(request, pending)
    else:
        _clear_pending_registration_session(request)
    return pending


def _send_password_reset_otp_email(user, otp_code):
    """Send a password reset OTP email."""
    if not user or not otp_code:
        return False

    try:
        subject = 'Password Reset OTP - Digital Gram Panchayat Portal'
        send_official_email(
            to_email=user.email,
            subject=subject,
            greeting_name='User',
            intro_text='We received a request to reset your account password.',
            body_lines=[
                'Use the OTP below to continue your password reset process.',
                'If you did not request a password reset, please ignore this message.'
            ],
            otp_code=otp_code,
            otp_expiry_minutes=5,
            help_text='For security assistance, please contact the portal help desk.',
        )
        return True
    except Exception:
        return False


def _send_registration_otp_email(pending_registration, otp_code):
    """Send OTP email for pending citizen registration."""
    if not pending_registration or not otp_code:
        return False

    try:
        subject = 'Registration OTP - Digital Gram Panchayat Portal'
        send_official_email(
            to_email=pending_registration.email,
            subject=subject,
            greeting_name='User',
            intro_text='Thank you for initiating registration with Digital Grampanchayat Portal.',
            body_lines=[
                'Please verify your email address using the OTP below to complete registration.',
                'For your protection, do not share this OTP with anyone.'
            ],
            otp_code=otp_code,
            otp_expiry_minutes=5,
            help_text='If you did not start this registration, please ignore this email.',
        )
        return True
    except Exception:
        return False


def _create_password_reset_otp(user):
    """Create a fresh OTP for password reset using the existing OTP model."""
    from .security_utils import generate_otp

    # Remove older OTP rows so verification always uses a single latest record.
    EmailOTP.objects.filter(user=user).delete()
    otp_code = generate_otp()
    otp = EmailOTP.objects.create(
        user=user,
        email=user.email,
        otp_code=otp_code,
        expires_at=timezone.now() + timedelta(minutes=5)
    )

    if hasattr(otp, 'set_otp_code'):
        otp.set_otp_code(otp_code)
        otp.save(update_fields=['otp_code_hash', 'otp_code'])

    otp.raw_otp_code = otp_code
    return otp


def log_user_activity(user, action, description, application=None, reference=''):
    """Record user activity timeline entries."""
    if not user:
        return None
    return UserActivity.objects.create(
        user=user,
        action=action,
        description=description,
        application=application,
        reference=reference or ''
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
    complaints = Complaint.objects.filter(complainant=user) if user else Complaint.objects.all()

    stats = {
    }
    return stats


def _get_recent_day_labels(total_days=30):
    """Return day labels and ordered date list for a rolling window."""
    today = timezone.localdate()
    date_markers = [today - timedelta(days=offset) for offset in range(total_days - 1, -1, -1)]

    if total_days <= 7:
        labels = [marker.strftime('%d %b') for marker in date_markers]
    else:
        labels = [marker.strftime('%d %b') if index % 5 == 0 else '' for index, marker in enumerate(date_markers)]
    return labels, date_markers


def _daily_counts(queryset, date_field, date_markers):
    """Return ordered daily counts matching provided date markers."""
    try:
        daily = (
            queryset
            .annotate(day=TruncDate(date_field))
            .values('day')
            .annotate(total=Count('id'))
        )
        lookup = {
            item['day'].strftime('%Y-%m-%d'): item['total']
            for item in daily
            if item.get('day')
        }
    except Exception:
        from collections import defaultdict
        lookup = defaultdict(int)
        dates = queryset.values_list(date_field, flat=True)
        for dt in dates:
            if dt:
                key = dt.strftime('%Y-%m-%d') if hasattr(dt, 'strftime') else str(dt)[:10]
                lookup[key] += 1
    return [lookup.get(marker.strftime('%Y-%m-%d'), 0) for marker in date_markers]


def _recent_month_labels(total_months=6):
    """Return ordered month labels and marker dates for recent months."""
    today = timezone.localdate().replace(day=1)
    markers = []
    cursor = today
    for _ in range(total_months):
        markers.append(cursor)
        if cursor.month == 1:
            cursor = cursor.replace(year=cursor.year - 1, month=12)
        else:
            cursor = cursor.replace(month=cursor.month - 1)

    markers.reverse()
    labels = [marker.strftime('%b %Y') for marker in markers]
    return labels, markers


def _monthly_counts(queryset, date_field, month_markers):
    """Return ordered monthly counts matching provided month markers."""
    try:
        monthly = (
            queryset
            .annotate(month=TruncMonth(date_field))
            .values('month')
            .annotate(total=Count('id'))
        )
        lookup = {
            item['month'].strftime('%Y-%m'): item['total']
            for item in monthly
            if item.get('month')
        }
    except Exception:
        from collections import defaultdict
        lookup = defaultdict(int)
        dates = queryset.values_list(date_field, flat=True)
        for dt in dates:
            if dt:
                key = dt.strftime('%Y-%m') if hasattr(dt, 'strftime') else str(dt)[:7]
                lookup[key] += 1
    return [lookup.get(marker.strftime('%Y-%m'), 0) for marker in month_markers]


def _build_dashboard_insights(role, total, pending, approved, rejected, top_category_label):
    """Generate role-aware insight cards for premium dashboard."""
    trend = 'Applications are stable this week.'
    if approved > pending:
        trend = 'Approvals are outpacing pending requests this week.'
    elif pending > approved:
        trend = 'Applications increased this week and pending queue is growing.'

    service = top_category_label or 'Income Certificate'
    queue = 'Backlog is healthy and under control.' if pending <= max(5, approved) else 'Pending queue needs attention for faster turnaround.'

    role_focus = {
        'admin': 'Admin focus: monitor users, complaints, and SLA trends.',
        'staff': 'Staff focus: resolve pending tasks and complaint updates quickly.',
        'citizen': 'Citizen focus: track your applications, bills, and complaints in one place.',
    }.get(role, 'Operational focus is balanced.')

    return [
        {
            'title': 'Weekly Trend',
            'message': trend,
            'icon': 'fas fa-chart-line',
            'accent': 'primary',
        },
        {
            'title': 'Most Used Service',
            'message': f'Most used service: {service}',
            'icon': 'fas fa-certificate',
            'accent': 'info',
        },
        {
            'title': 'Queue Health',
            'message': queue,
            'icon': 'fas fa-layer-group',
            'accent': 'warning',
        },
        {
            'title': 'Role Insight',
            'message': role_focus,
            'icon': 'fas fa-lightbulb',
            'accent': 'success',
        },
    ]


@login_required
def dashboard_data_api(request):
    """Return role-aware dashboard charts and metric counters from database."""
    selected_days = request.GET.get('days', '30')
    if selected_days not in ['7', '30', '90']:
        selected_days = '30'
    window_days = int(selected_days)

    labels, date_markers = _get_recent_day_labels(window_days)
    start_date = date_markers[0]
    start_dt = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    role = request.user.role

    if role == 'admin':
        applications_qs = Application.objects.all()
        complaints_qs = Complaint.objects.all()
        users_qs = CustomUser.objects.filter(role='citizen')
    elif role == 'staff':
        applications_qs = Application.objects.all()
        complaints_qs = Complaint.objects.all()
        users_qs = CustomUser.objects.filter(role='citizen')
    else:
        applications_qs = Application.objects.filter(applicant=request.user)
        complaints_qs = Complaint.objects.filter(complainant=request.user)
        users_qs = Application.objects.filter(applicant=request.user)

    month_labels, month_markers = _recent_month_labels(6)

    if role in ['admin', 'staff']:
        line_values = _monthly_counts(users_qs, 'date_joined', month_markers)
    else:
        line_values = _monthly_counts(
            Application.objects.filter(applicant=request.user),
            'applied_date',
            month_markers,
        )

    filtered_applications = applications_qs.filter(applied_date__gte=start_dt)
    filtered_complaints = complaints_qs.filter(filed_date__gte=start_dt)

    category_rows = (
        filtered_applications
        .values('application_type')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    bar_labels = []
    bar_values = []
    for row in category_rows:
        label = row['application_type'].replace('_', ' ').title()
        bar_labels.append(label)
        bar_values.append(row['total'])

    if not bar_labels:
        bar_labels = ['No Data']
        bar_values = [0]

    pie_values = [
        filtered_applications.filter(status='approved').count(),
        filtered_applications.filter(status='pending').count(),
        filtered_applications.filter(status='rejected').count(),
    ]

    pie_labels = ['Approved', 'Pending', 'Rejected']

    metrics = {
        'total_applications': filtered_applications.count(),
        'pending_applications': filtered_applications.filter(status='pending').count(),
        'approved_applications': filtered_applications.filter(status='approved').count(),
        'rejected_applications': filtered_applications.filter(status='rejected').count(),
        'complaints_open': filtered_complaints.filter(status='open').count(),
        'complaints_in_progress': filtered_complaints.filter(status='in_progress').count(),
    }

    return JsonResponse({
        'days': window_days,
        'labels': labels,
        'line_labels': month_labels,
        'bar_labels': bar_labels,
        'pie_labels': pie_labels,
        'line': line_values,
        'bar': bar_values,
        'pie': pie_values,
        'metrics': metrics,
    })


def _build_demo_amount(identifier, base_value):
    """Return deterministic demo amount from an identifier."""
    seed = sum(ord(c) for c in identifier)
    return round(base_value + (seed % 700), 2)


def _build_application_approval_pdf(application):
    """Build PDF bytes for approved application/certificate."""
    if application.application_type in ['birth_certificate', 'death_certificate', 'income_certificate']:
        return generate_marathi_certificate(None, application)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.setFont('Helvetica-Bold', 16)
    p.drawString(70, 800, 'Digital Gram Panchayat')
    p.setFont('Helvetica', 12)
    p.drawString(70, 775, 'Application Approval Letter')

    y = 735
    lines = [
        f"Application Number: {application.application_number}",
        f"Applicant: {application.applicant.get_full_name()}",
        f"Application Type: {application.get_application_type_display()}",
        f"Status: {application.get_status_display()}",
        f"Approved On: {timezone.now().strftime('%d-%m-%Y %H:%M')}",
    ]

    if application.application_type == 'complaint_submission' and hasattr(application, 'complaint_record'):
        complaint = application.complaint_record
        lines.extend([
            f"Complaint Number: {complaint.complaint_number}",
            f"Subject: {complaint.subject}",
        ])
    elif application.application_type == 'bill_request' and hasattr(application, 'bill_request'):
        bill_request = application.bill_request
        lines.extend([
            f"Bill Request Type: {bill_request.get_request_type_display()}",
            f"Reference: {bill_request.account_or_consumer_number}",
            f"Subject: {bill_request.subject}",
        ])

    for line in lines:
        p.drawString(70, y, line)
        y -= 24

    p.setFont('Helvetica-Oblique', 10)
    p.drawString(70, 100, 'This is a system-generated approval document.')
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue()


def _save_application_pdf(application):
    """Generate and persist application PDF in media, then return the FieldFile."""
    pdf_bytes = _build_application_approval_pdf(application)
    if not pdf_bytes:
        return None

    filename = f"{application.application_number}.pdf"
    application.certificate_pdf.save(filename, ContentFile(pdf_bytes), save=False)
    return application.certificate_pdf


def _send_approval_email_with_pdf(application):
    """Send approval email with generated certificate PDF attachment."""
    recipient = application.applicant.email
    if not recipient:
        return False, 'Applicant email is missing.'

    if not application.certificate_pdf:
        return False, 'PDF is not available for attachment.'

    subject = f"{application.get_application_type_display()} Approved - {application.application_number}"

    try:
        with application.certificate_pdf.open('rb') as certificate_file:
            pdf_content = certificate_file.read()

        send_official_email(
            to_email=recipient,
            subject=subject,
            greeting_name='User',
            intro_text=f"Your {application.get_application_type_display()} request has been approved.",
            body_lines=[
                'Your approved certificate/document is attached to this email.',
                'You may also download it from the My Certificates section in the portal.'
            ],
            reference_text=f"Application Number: {application.application_number} | Status: Approved",
            attachments=[
                (
                    f"{application.application_number}.pdf",
                    pdf_content,
                    'application/pdf',
                )
            ],
            help_text='For any clarification, please contact the Grampanchayat office.'
        )
        return True, ''
    except Exception as exc:
        return False, str(exc)


def email_template_preview(request):
    """Render a live browser preview of the official email template."""
    preview_html = render_to_string(
        'portal_app/emails/official_notification.html',
        {
            'portal_title': 'Digital Grampanchayat Portal',
            'greeting_name': 'User',
            'subject_title': 'Registration OTP - Digital Grampanchayat Portal',
            'intro_text': 'This is a live preview of the official email layout used by the portal.',
            'body_lines': [
                'Please verify your email address using the OTP below.',
                'This communication style is applied to OTP, password reset, and notification emails.'
            ],
            'otp_code': '824613',
            'otp_expiry_minutes': 5,
            'cta_text': 'Open Portal',
            'cta_url': request.build_absolute_uri(reverse('home')),
            'reference_text': 'Reference: PREVIEW-EMAIL-2026',
            'help_text': 'For assistance, please contact support at support@grampanchayat.gov.in.',
            'footer_note': 'This is an official communication from Digital Grampanchayat Portal.',
            'logo_data_uri': PORTAL_LOGO_DATA_URI,
        },
    )
    return render(request, 'portal_app/email_preview.html', {'preview_html': preview_html})


# ============================================
# PUBLIC VIEWS
# ============================================

def access_denied(request):
    """
    Access denied page for unauthorized access attempts
    """
    return render(request, 'portal_app/access_denied.html')


def _is_protected_main_admin(user):
    """Return True when an admin account should be protected from deletion."""
    if not user or user.role != 'admin':
        return False

    if user.is_superuser:
        return True

    main_admin = CustomUser.objects.filter(role='admin').order_by('created_at').first()
    return bool(main_admin and main_admin.pk == user.pk)


def _attach_cropped_profile_image(user, image_data):
    """Decode base64 cropped image and attach it to user's profile photo."""
    if not image_data or not image_data.startswith('data:image/'):
        return False

    try:
        header, encoded = image_data.split(',', 1)
        mime = header.split(';')[0].split(':')[1].strip().lower()
        extension_map = {
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg',
            'image/png': 'png',
            'image/webp': 'webp',
        }
        extension = extension_map.get(mime)
        if not extension:
            return False

        binary = base64.b64decode(encoded)
        filename = f"profile_{user.pk}_{uuid.uuid4().hex[:10]}.{extension}"

        if user.profile_photo:
            user.profile_photo.delete(save=False)
        user.profile_photo.save(filename, ContentFile(binary), save=False)
        return True
    except (ValueError, IndexError, binascii.Error):
        return False


@login_required
@require_http_methods(["GET", "POST"])
def account_settings(request):
    """Advanced account settings page for all roles with role-safe controls."""
    active_tab = request.GET.get('tab', 'profile')
    settings_form = UserSettingsForm(instance=request.user)
    password_form = UserPasswordChangeForm(user=request.user)
    delete_form = AccountDeleteForm()

    if request.method == 'POST':
        action = request.POST.get('action', 'profile').strip()
        active_tab = request.POST.get('active_tab', active_tab).strip() or 'profile'

        if action == 'profile':
            active_tab = 'profile'
            settings_form = UserSettingsForm(request.POST, request.FILES, instance=request.user)
            password_form = UserPasswordChangeForm(user=request.user)
            delete_form = AccountDeleteForm()

            if settings_form.is_valid():
                user = settings_form.save(commit=False)
                cropped_data = request.POST.get('profile_photo_cropped', '').strip()

                if cropped_data and not _attach_cropped_profile_image(user, cropped_data):
                    messages.error(request, 'Invalid cropped image format. Please try again.')
                else:
                    user.save()
                    log_user_activity(
                        user=request.user,
                        action='profile_updated',
                        description='Updated profile information in account settings.',
                        reference=request.user.username,
                    )
                    messages.success(request, 'Profile updated successfully.')
                    return redirect(f"{reverse('settings')}?tab=profile")
            else:
                messages.error(request, 'Please correct the profile errors below.')

        elif action == 'password':
            active_tab = 'password'
            settings_form = UserSettingsForm(instance=request.user)
            password_form = UserPasswordChangeForm(request.POST, user=request.user)
            delete_form = AccountDeleteForm()

            if password_form.is_valid():
                new_password = password_form.cleaned_data['new_password1']
                request.user.set_password(new_password)
                request.user.save(update_fields=['password'])
                update_session_auth_hash(request, request.user)

                log_user_activity(
                    user=request.user,
                    action='password_changed',
                    description='Changed account password from settings.',
                    reference=request.user.username,
                )
                messages.success(request, 'Password changed successfully.')
                return redirect(f"{reverse('settings')}?tab=password")
            messages.error(request, 'Please correct the password errors below.')

        elif action == 'delete':
            active_tab = 'profile'
            settings_form = UserSettingsForm(instance=request.user)
            password_form = UserPasswordChangeForm(user=request.user)
            delete_form = AccountDeleteForm(request.POST)

            if _is_protected_main_admin(request.user):
                messages.error(request, 'Main admin account is protected and cannot be deleted.')
                return redirect(f"{reverse('settings')}?tab=profile")

            if delete_form.is_valid():
                user_name = request.user.get_full_name() or request.user.username
                log_user_activity(
                    user=request.user,
                    action='account_deleted',
                    description='Requested and completed self account deletion.',
                    reference=request.user.username,
                )
                request.user.delete()
                logout(request)
                messages.success(request, f'Your account ({user_name}) has been deleted successfully.')
                return redirect('home')
            messages.error(request, 'Account deletion confirmation failed.')
        else:
            messages.error(request, 'Invalid settings action requested.')

    recent_activities = UserActivity.objects.filter(user=request.user).order_by('-created_at')[:25]
    can_delete_account = not _is_protected_main_admin(request.user)

    context = {
        'title': 'Settings',
        'settings_form': settings_form,
        'password_form': password_form,
        'delete_form': delete_form,
        'recent_activities': recent_activities,
        'active_tab': active_tab,
        'can_delete_account': can_delete_account,
    }
    return render(request, 'portal_app/settings.html', context)


@login_required
@require_POST
def delete_account(request):
    """Delete the current account after confirmation."""
    if _is_protected_main_admin(request.user):
        messages.error(request, 'Main admin account is protected and cannot be deleted.')
        return redirect('settings')

    form = AccountDeleteForm(request.POST)
    if form.is_valid():
        user_name = request.user.get_full_name() or request.user.username
        log_user_activity(
            user=request.user,
            action='account_deleted',
            description='Requested and completed self account deletion.',
            reference=request.user.username,
        )
        request.user.delete()
        logout(request)
        messages.success(request, f'Your account ({user_name}) has been deleted successfully.')
        return redirect('home')

    messages.error(request, 'Account deletion confirmation failed.')
    return redirect('settings')


@require_http_methods(["GET", "POST"])
def forgot_password_view(request):
    """Start forgot-password flow by sending OTP to registered email."""
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('admin_dashboard')
        if request.user.role == 'staff':
            return redirect('staff_dashboard')
        return redirect('dashboard')

    form = ForgotPasswordRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip().lower()
        user = CustomUser.objects.filter(email__iexact=email, role__in=['citizen', 'staff']).first()

        if not user:
            messages.error(request, 'No citizen or staff account found for this email.')
            return render(request, 'portal_app/forgot_password.html', {'title': 'Forgot Password', 'form': form})

        otp = _create_password_reset_otp(user)
        if not _send_password_reset_otp_email(user, getattr(otp, 'raw_otp_code', None)):
            messages.error(request, 'Unable to send OTP right now. Please try again.')
            return render(request, 'portal_app/forgot_password.html', {'title': 'Forgot Password', 'form': form})

        request.session['password_reset_user_id'] = user.id
        request.session['password_reset_otp_sent_at'] = timezone.now().isoformat()
        request.session['password_reset_verified_user_id'] = None
        request.session.modified = True
        messages.success(request, f'OTP sent to {user.email}. Please verify within 5 minutes.')
        return redirect('forgot_password_verify_otp')

    return render(request, 'portal_app/forgot_password.html', {'title': 'Forgot Password', 'form': form})


@require_http_methods(["GET", "POST"])
def forgot_password_verify_otp_view(request):
    """Verify the OTP sent for password reset."""
    user_id = request.session.get('password_reset_user_id')
    if not user_id:
        messages.error(request, 'Password reset session not found. Please start again.')
        return redirect('forgot_password')

    user = get_object_or_404(CustomUser, id=user_id)

    latest_otp = EmailOTP.objects.filter(user=user, is_used=False).order_by('-created_at').first()
    form = OTPVerificationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        from .security_utils import verify_otp
        success, message = verify_otp(user, form.cleaned_data['otp_code'])
        if success:
            request.session['password_reset_verified_user_id'] = user.id
            request.session.modified = True
            messages.success(request, 'OTP verified. You can now set a new password.')
            return redirect('forgot_password_set_new_password')
        messages.error(request, message)

    time_remaining = latest_otp.get_time_remaining() if latest_otp and latest_otp.is_valid() else 0
    minutes = time_remaining // 60
    seconds = time_remaining % 60

    context = {
        'title': 'Verify OTP',
        'form': form,
        'email': user.email,
        'time_remaining': time_remaining,
        'minutes': minutes,
        'seconds': seconds,
        'attempts_left': max(0, 3 - (latest_otp.verification_attempts if latest_otp else 0)),
        'otp_exists': latest_otp is not None,
    }
    return render(request, 'portal_app/forgot_password_verify.html', context)


@require_POST
def forgot_password_resend_otp_view(request):
    """Resend password reset OTP."""
    user_id = request.session.get('password_reset_user_id')
    if not user_id:
        messages.error(request, 'Password reset session not found. Please start again.')
        return redirect('forgot_password')

    user = get_object_or_404(CustomUser, id=user_id)
    recent_otp = EmailOTP.objects.filter(
        user=user,
        created_at__gte=timezone.now() - timedelta(seconds=60)
    ).first()
    if recent_otp:
        messages.error(request, 'Please wait 1 minute before requesting a new OTP.')
        return redirect('forgot_password_verify_otp')

    otp = _create_password_reset_otp(user)
    if _send_password_reset_otp_email(user, getattr(otp, 'raw_otp_code', None)):
        request.session['password_reset_otp_sent_at'] = timezone.now().isoformat()
        request.session.modified = True
        messages.success(request, f'New OTP sent to {user.email}.')
    else:
        messages.error(request, 'Unable to resend OTP right now. Please try again.')
    return redirect('forgot_password_verify_otp')


@require_http_methods(["GET", "POST"])
def forgot_password_set_new_password_view(request):
    """Set a new password after OTP verification."""
    verified_user_id = request.session.get('password_reset_verified_user_id')
    if not verified_user_id:
        messages.error(request, 'Please verify OTP before setting a new password.')
        return redirect('forgot_password')

    user = get_object_or_404(CustomUser, id=verified_user_id)
    form = PasswordResetForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user.set_password(form.cleaned_data['new_password1'])
        user.save(update_fields=['password'])

        request.session.pop('password_reset_user_id', None)
        request.session.pop('password_reset_verified_user_id', None)
        request.session.pop('password_reset_otp_sent_at', None)
        messages.success(request, 'Password updated successfully. Please login with your new password.')
        return redirect('login')

    context = {
        'title': 'Set New Password',
        'form': form,
        'email': user.email,
    }
    return render(request, 'portal_app/forgot_password_reset.html', context)


def home(request):
    """
    Homepage - Public view
    """
    total_users = CustomUser.objects.filter(role='citizen').count()
    total_services = 6
    total_certificates = Application.objects.filter(
        application_type__in=['birth_certificate', 'death_certificate', 'income_certificate'],
        status='approved'
    ).count()

    service_overview = [
        {
            'title': 'Income Certificate',
            'icon': 'bi-cash-coin',
            'description': 'Apply online for income certificate with document verification and status tracking.',
            'url_name': 'apply_income_certificate',
            'requires_login': True,
        },
        {
            'title': 'Birth Certificate',
            'icon': 'bi-file-earmark-medical',
            'description': 'Register and apply for birth certificate through a guided digital process.',
            'url_name': 'apply_birth_certificate',
            'requires_login': True,
        },
        {
            'title': 'Death Certificate',
            'icon': 'bi-file-earmark-x',
            'description': 'Submit death registration requests and track verification from your account.',
            'url_name': 'apply_death_certificate',
            'requires_login': True,
        },
        {
            'title': 'Electricity Bill',
            'icon': 'bi-lightning-charge-fill',
            'description': 'View bill details and complete payment workflows from one secure page.',
            'url_name': 'electricity_bill_service',
            'requires_login': True,
        },
        {
            'title': 'Water Bill',
            'icon': 'bi-droplet-half',
            'description': 'Access water billing module with due-date tracking and receipt support.',
            'url_name': 'water_bill_service',
            'requires_login': True,
        },
        {
            'title': 'Complaint Registration',
            'icon': 'bi-chat-square-dots-fill',
            'description': 'Register complaints, submit details, and follow resolution updates in one place.',
            'url_name': 'file_complaint',
            'requires_login': True,
        },
    ]

    announcements = [
        {
            'title': 'Public Service Window Timings Updated',
            'date': '06 Apr 2026',
            'body': 'Citizen help desk now remains open from 9:30 AM to 6:00 PM on all working days.',
            'tag': 'Office Notice',
        },
        {
            'title': 'Online Certificate Priority Processing',
            'date': '03 Apr 2026',
            'body': 'Income, birth, and death certificate applications submitted online will receive priority scrutiny.',
            'tag': 'Citizen Update',
        },
        {
            'title': 'Bill Payment Support Desk',
            'date': '01 Apr 2026',
            'body': 'Dedicated support has been enabled for electricity and water bill related requests.',
            'tag': 'Utility Notice',
        },
    ]

    context = {
        'title': 'Home',
        'service_overview': service_overview,
        'announcements': announcements,
        'stats': {
            'users': total_users,
            'services': total_services,
            'certificates': total_certificates,
        },
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
    service_cards = [
        {
            'title': 'Income Certificate',
            'icon': 'bi-cash-coin',
            'description': 'Apply for income certificate for scholarships, welfare schemes, and concessions.',
            'url_name': 'apply_income_certificate',
            'button': 'Apply Now',
        },
        {
            'title': 'Birth Certificate',
            'icon': 'bi-file-earmark-medical-fill',
            'description': 'Submit child birth details online and get official certificate after verification.',
            'url_name': 'apply_birth_certificate',
            'button': 'Apply Now',
        },
        {
            'title': 'Death Certificate',
            'icon': 'bi-file-earmark-x-fill',
            'description': 'Complete death registration and receive digital certificate for legal processes.',
            'url_name': 'apply_death_certificate',
            'button': 'Apply Now',
        },
        {
            'title': 'Electricity Bill',
            'icon': 'bi-lightning-charge-fill',
            'description': 'Check bill amount, due date, and status with payment support features.',
            'url_name': 'electricity_bill_service',
            'button': 'Apply Now',
        },
        {
            'title': 'Water Bill',
            'icon': 'bi-droplet-half',
            'description': 'Access water billing records, payment status, and downloadable bill documents.',
            'url_name': 'water_bill_service',
            'button': 'Apply Now',
        },
        {
            'title': 'Complaint Registration',
            'icon': 'bi-chat-square-dots-fill',
            'description': 'Register complaints, submit details, and follow resolution updates in one place.',
            'url_name': 'file_complaint',
            'button': 'Apply Now',
        },
    ]

    context = {
        'title': 'Services',
        'service_cards': service_cards,
    }
    return render(request, 'portal_app/services.html', context)


@login_required
def notifications_api(request):
    """Return latest notifications for navbar bell dropdown polling."""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10]
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()

    payload = {
        'unread_count': unread_count,
        'items': [
            {
                'id': item.id,
                'title': _(item.title),
                'message': _(item.message),
                'category': item.category,
                'is_read': item.is_read,
                'target_url': item.target_url,
                'created_at': item.created_at.strftime('%d %b %Y, %H:%M'),
            }
            for item in notifications
        ]
    }
    return JsonResponse(payload)


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a single notification as read."""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def mark_all_notifications_read(request):
    """Mark all notifications as read for current user."""
    Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    return JsonResponse({'ok': True})


@login_required
def smart_search_api(request):
    """Live search for services, applications, and complaints."""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'query': query, 'results': []})

    query_lower = query.lower()
    results = []

    service_items = [
        {'title': 'Birth Certificate', 'url': reverse('apply_birth_certificate'), 'kind': 'service'},
        {'title': 'Death Certificate', 'url': reverse('apply_death_certificate'), 'kind': 'service'},
        {'title': 'Income Certificate', 'url': reverse('apply_income_certificate'), 'kind': 'service'},
        {'title': 'File Complaint', 'url': reverse('file_complaint'), 'kind': 'service'},
        {'title': 'Electricity Bill', 'url': reverse('electricity_bill_service'), 'kind': 'service'},
        {'title': 'Water Bill', 'url': reverse('water_bill_service'), 'kind': 'service'},
        {'title': 'Property Tax', 'url': reverse('property_tax_service'), 'kind': 'service'},
        {'title': 'My Certificates', 'url': reverse('my_certificates'), 'kind': 'document'},
    ]

    for item in service_items:
        if query_lower in item['title'].lower():
            results.append(item)

    if request.user.role in ['staff', 'admin']:
        application_qs = Application.objects.filter(
            Q(application_number__icontains=query) |
            Q(application_type__icontains=query) |
            Q(applicant__username__icontains=query) |
            Q(applicant__first_name__icontains=query) |
            Q(applicant__last_name__icontains=query)
        )
        complaint_qs = Complaint.objects.filter(
            Q(complaint_number__icontains=query) |
            Q(subject__icontains=query) |
            Q(complainant__username__icontains=query)
        )
    else:
        application_qs = Application.objects.filter(
            applicant=request.user
        ).filter(
            Q(application_number__icontains=query) |
            Q(application_type__icontains=query)
        )
        complaint_qs = Complaint.objects.filter(
            complainant=request.user
        ).filter(
            Q(complaint_number__icontains=query) |
            Q(subject__icontains=query)
        )

    for application in application_qs.select_related('applicant')[:6]:
        app_url = (
            reverse('admin_review_application', kwargs={'application_id': application.id})
            if request.user.role in ['staff', 'admin']
            else reverse('application_detail', kwargs={'application_id': application.id})
        )
        results.append({
            'title': application.application_number,
            'subtitle': f"{application.get_application_type_display()} - {application.get_status_display()}",
            'url': app_url,
            'kind': 'application',
        })

    for complaint in complaint_qs.select_related('complainant')[:6]:
        complaint_url = (
            reverse('admin_update_complaint', kwargs={'complaint_id': complaint.id})
            if request.user.role in ['staff', 'admin']
            else reverse('complaint_detail', kwargs={'complaint_id': complaint.id})
        )
        results.append({
            'title': complaint.complaint_number,
            'subtitle': f"{complaint.subject} - {complaint.get_status_display()}",
            'url': complaint_url,
            'kind': 'complaint',
        })

    return JsonResponse({'query': query, 'results': results[:12]})


@csrf_exempt
@require_POST
def chatbot_api(request):
    """Help desk chatbot with intent handling and live record lookups."""
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'reply': 'Sorry, I could not read that message. Please try again 😊'}, status=400)

    user_message = str(payload.get('message', '')).strip()
    if not user_message:
        return JsonResponse({'reply': 'Please type your question, and I will help you 😊'}, status=400)

    response_data = build_chatbot_response(request, user_message)
    status_code = int(response_data.pop('status', 200) or 200)
    return JsonResponse(response_data, status=status_code)

    text = user_message.lower()

    upper_text = user_message.upper()
    app_number_match = re.search(r'\bGP[A-Z]{4}\d{8,}\b', upper_text)
    complaint_number_match = re.search(r'\bCMP\d{8,}\b', upper_text)

    is_authenticated = request.user.is_authenticated
    is_staff_or_admin = is_authenticated and request.user.role in ['staff', 'admin']

    wants_apply_steps = any(word in text for word in ['how to apply', 'apply', 'steps', 'process'])

    assistant_service_actions = {
        'income_certificate': {
            'service': 'income_certificate',
            'title': 'Income Certificate Application',
            'url': reverse('apply_income_certificate'),
            'steps': [
                'Confirm applicant details',
                'Fill income details',
                'Upload required documents',
                'Submit application',
            ],
            'prefill': ['name', 'email', 'phone'],
        },
        'birth_certificate': {
            'service': 'birth_certificate',
            'title': 'Birth Certificate Application',
            'url': reverse('apply_birth_certificate'),
            'steps': [
                'Enter child details',
                'Enter parent details',
                'Upload supporting documents',
                'Submit application',
            ],
            'prefill': ['name', 'email', 'phone'],
        },
        'death_certificate': {
            'service': 'death_certificate',
            'title': 'Death Certificate Application',
            'url': reverse('apply_death_certificate'),
            'steps': [
                'Enter deceased details',
                'Add informant details',
                'Upload supporting documents',
                'Submit application',
            ],
            'prefill': ['name', 'email', 'phone'],
        },
        'complaint': {
            'service': 'complaint',
            'title': 'File Complaint',
            'url': reverse('file_complaint'),
            'steps': [
                'Choose category',
                'Describe issue',
                'Upload evidence (optional)',
                'Submit complaint',
            ],
            'prefill': ['name', 'email', 'phone'],
        },
        'electricity_bill': {
            'service': 'electricity_bill',
            'title': 'Electricity Bill Service',
            'url': reverse('electricity_bill_service'),
            'steps': [
                'Enter consumer number',
                'Verify bill details',
                'Proceed with payment',
            ],
            'prefill': ['name', 'email', 'phone'],
        },
        'water_bill': {
            'service': 'water_bill',
            'title': 'Water Bill Service',
            'url': reverse('water_bill_service'),
            'steps': [
                'Enter connection number',
                'Verify bill details',
                'Proceed with payment',
            ],
            'prefill': ['name', 'email', 'phone'],
        },
        'property_tax': {
            'service': 'property_tax',
            'title': 'Property Tax Service',
            'url': reverse('property_tax_service'),
            'steps': [
                'Search property',
                'Verify dues',
                'Proceed with payment',
            ],
            'prefill': ['name', 'email', 'phone'],
        },
    }

    if is_authenticated and any(word in text for word in ['apply', 'open', 'start', 'file', 'pay', 'submit']):
        action_key = None
        if 'income' in text and 'certificate' in text:
            action_key = 'income_certificate'
        elif 'birth' in text and 'certificate' in text:
            action_key = 'birth_certificate'
        elif 'death' in text and 'certificate' in text:
            action_key = 'death_certificate'
        elif any(word in text for word in ['complaint', 'grievance', 'issue']):
            action_key = 'complaint'
        elif any(word in text for word in ['electricity', 'light', 'power', 'current']) and 'bill' in text:
            action_key = 'electricity_bill'
        elif 'water' in text and 'bill' in text:
            action_key = 'water_bill'
        elif ('property' in text and 'tax' in text) or ('property' in text and 'bill' in text):
            action_key = 'property_tax'

        if action_key:
            action = assistant_service_actions[action_key]
            return JsonResponse({
                'reply': (
                    f"Opening {action['title']} now. "
                    "I will prefill known details, highlight required fields, and guide you step-by-step."
                ),
                'action': action,
            })

    if ('income' in text and wants_apply_steps):
        reply = (
            "Sure! 😊\n"
            "To apply for an income certificate, follow these steps:\n\n"
            "1. Go to the Services section\n"
            "2. Select Income Certificate\n"
            "3. Fill in your personal and income details\n"
            "4. Upload the required documents\n"
            "5. Submit the form\n\n"
            "After submission, you can track it from My Applications."
        )
        return JsonResponse({'reply': reply})

    if ('birth' in text and wants_apply_steps):
        reply = (
            "Of course 😊\n"
            "To apply for a birth certificate:\n\n"
            "1. Open Services\n"
            "2. Choose Birth Certificate\n"
            "3. Enter child and parent details\n"
            "4. Upload supporting documents\n"
            "5. Submit and save your application number\n\n"
            "You can track updates in My Applications."
        )
        return JsonResponse({'reply': reply})

    if ('death' in text and wants_apply_steps):
        reply = (
            "I can help with that 😊\n"
            "To apply for a death certificate:\n\n"
            "1. Go to Services\n"
            "2. Select Death Certificate\n"
            "3. Fill deceased and informant details\n"
            "4. Upload required proof\n"
            "5. Submit the application\n\n"
            "Then check progress from My Applications."
        )
        return JsonResponse({'reply': reply})

    if (any(word in text for word in ['complaint', 'grievance', 'issue']) and wants_apply_steps):
        reply = (
            "Sure, here is how to file a complaint 😊\n\n"
            "1. Open Services\n"
            "2. Click File Complaint\n"
            "3. Select category and location\n"
            "4. Describe the issue clearly\n"
            "5. Upload photo (if available) and submit\n\n"
            "You can follow updates from My Complaints."
        )
        return JsonResponse({'reply': reply})

    if app_number_match:
        application_number = app_number_match.group(0)
        app_qs = Application.objects.filter(application_number=application_number)
        if is_authenticated and not is_staff_or_admin:
            app_qs = app_qs.filter(applicant=request.user)

        application = app_qs.first()
        if application:
            reviewed_text = (
                f"Reviewed on {application.reviewed_date.strftime('%d %b %Y')}."
                if application.reviewed_date else 'It is currently being processed.'
            )
            detail_url = (
                reverse('admin_review_application', kwargs={'application_id': application.id})
                if is_staff_or_admin else reverse('application_detail', kwargs={'application_id': application.id})
            )
            reply = (
                "I checked that for you 😊\n\n"
                f"- Application ID: {application.application_number}\n"
                f"- Current status: {application.get_status_display()}\n"
                f"- Service: {application.get_application_type_display()}\n"
                f"- Note: {reviewed_text}\n\n"
                f"You can open full details here: {detail_url}"
            )
        else:
            reply = (
                f"I could not find application {application_number}.\n"
                "Please check the number once and try again, or open Track Application 😊"
            )
        return JsonResponse({'reply': reply})

    if complaint_number_match:
        complaint_number = complaint_number_match.group(0)
        complaint_qs = Complaint.objects.filter(complaint_number=complaint_number)
        if is_authenticated and not is_staff_or_admin:
            complaint_qs = complaint_qs.filter(complainant=request.user)

        complaint = complaint_qs.first()
        if complaint:
            detail_url = (
                reverse('admin_update_complaint', kwargs={'complaint_id': complaint.id})
                if is_staff_or_admin else reverse('complaint_detail', kwargs={'complaint_id': complaint.id})
            )
            reply = (
                "I found your complaint details 😊\n\n"
                f"- Complaint ID: {complaint.complaint_number}\n"
                f"- Current status: {complaint.get_status_display()}\n"
                f"- Priority: {complaint.get_priority_display()}\n\n"
                f"You can view full details here: {detail_url}"
            )
        else:
            reply = (
                f"I could not find complaint {complaint_number}.\n"
                "Please verify the complaint number or check My Complaints 😊"
            )
        return JsonResponse({'reply': reply})

    if not is_authenticated and any(word in text for word in [
        'my application', 'my complaint', 'status', 'track', 'bill', 'tax', 'my certificate', 'dashboard'
    ]):
        return JsonResponse({
            'reply': (
                "I can check that for you 😊\n"
                "Please login first, then I will show your application, complaint, certificate, and bill details."
            )
        })

    if 'status' in text and is_authenticated and not (app_number_match or complaint_number_match):
        return JsonResponse({
            'reply': (
                "Let me help you with status 😊\n\n"
                "- For certificates and applications: open My Applications\n"
                "- For grievances: open My Complaints\n"
                "- For exact tracking: share your GP or CMP number"
            )
        })

    if any(word in text for word in ['my applications', 'application status', 'pending application', 'track application', 'application']) and is_authenticated:
        user_apps = Application.objects.filter(applicant=request.user)
        total = user_apps.count()
        pending = user_apps.filter(status='pending').count()
        review = user_apps.filter(status='under_review').count()
        latest = user_apps.order_by('-applied_date').first()
        if total == 0:
            reply = (
                "You do not have any applications yet 😊\n\n"
                "To start:\n"
                "1. Go to Services\n"
                "2. Choose the certificate/service\n"
                "3. Submit the form"
            )
        else:
            processing_note = "You have applications in progress." if (pending + review) > 0 else "Your recent applications are completed."
            latest_line = (
                f"Most recent: {latest.application_number} ({latest.get_status_display()})."
                if latest else ""
            )
            reply = (
                "Here is a quick update on your applications 😊\n\n"
                f"- {processing_note}\n"
                f"- {latest_line}\n\n"
                "For full details, open My Applications."
            )
        return JsonResponse({'reply': reply})

    if any(word in text for word in ['my complaints', 'complaint status', 'complaint', 'grievance', 'issue']) and is_authenticated:
        user_complaints = Complaint.objects.filter(complainant=request.user)
        total = user_complaints.count()
        open_count = user_complaints.filter(status='open').count()
        progress_count = user_complaints.filter(status='in_progress').count()
        latest = user_complaints.order_by('-filed_date').first()
        if total == 0:
            reply = (
                "You have not filed any complaints yet 😊\n\n"
                "If you want, I can guide you to submit one in a few steps."
            )
        else:
            active_note = "You still have active complaints." if (open_count + progress_count) > 0 else "Your complaints look resolved."
            latest_line = (
                f"Latest complaint: {latest.complaint_number} ({latest.get_status_display()})."
                if latest else ""
            )
            reply = (
                "Here is your complaint update 😊\n\n"
                f"- {active_note}\n"
                f"- {latest_line}\n\n"
                "You can open My Complaints for complete details."
            )
        return JsonResponse({'reply': reply})

    if any(word in text for word in ['bill', 'tax', 'electricity', 'water', 'property']) and is_authenticated:
        e_pending = ElectricityBill.objects.filter(user=request.user, payment_status__in=['pending', 'overdue'])
        w_pending = WaterBill.objects.filter(user=request.user, payment_status__in=['pending', 'overdue'])
        p_pending = PropertyTaxRecord.objects.filter(user=request.user, payment_status__in=['pending', 'overdue'])

        e_total = e_pending.aggregate(total=Sum('amount'))['total'] or 0
        w_total = w_pending.aggregate(total=Sum('amount'))['total'] or 0
        p_total = p_pending.aggregate(total=Sum('tax_amount'))['total'] or 0

        grand_total = e_total + w_total + p_total
        lines = []
        if e_pending.exists():
            lines.append('- You have pending electricity bill entries.')
        if w_pending.exists():
            lines.append('- You have pending water bill entries.')
        if p_pending.exists():
            lines.append('- You have pending property tax entries.')

        if not lines:
            reply = (
                "Great news 😊\n"
                "I could not find any pending electricity, water, or property tax dues right now."
            )
        else:
            reply = (
                "I checked your bill and tax records 😊\n\n"
                + "\n".join(lines)
                + f"\n\nEstimated total due: INR {grand_total:.2f}.\n"
                "You can clear dues from the Services section."
            )
        return JsonResponse({'reply': reply})

    if any(word in text for word in ['certificate', 'birth', 'death', 'income']) and is_authenticated:
        cert_apps = Application.objects.filter(
            applicant=request.user,
            application_type__in=['birth_certificate', 'death_certificate', 'income_certificate']
        )
        pending = cert_apps.filter(status__in=['pending', 'under_review']).count()
        if cert_apps.exists():
            progress_line = "Some certificate requests are still in process." if pending > 0 else "Your recent certificate requests are completed."
            reply = (
                "Here is your certificate update 😊\n\n"
                f"- {progress_line}\n"
                "- You can track each request in My Applications\n"
                "- You can submit a new request from Services anytime"
            )
        else:
            reply = (
                "You have not applied for a certificate yet 😊\n\n"
                "Available services:\n"
                "- Birth Certificate\n"
                "- Death Certificate\n"
                "- Income Certificate\n\n"
                "Open Services to start."
            )
        return JsonResponse({'reply': reply})

    if any(word in text for word in ['login', 'register', 'otp', 'verification', 'password']):
        reply = (
            "Sure, here is the quick login help 😊\n\n"
            "1. New user: use Register\n"
            "2. Existing user: use Login\n"
            "3. If OTP is delayed: click Resend OTP\n\n"
            "If you want, I can guide you step-by-step."
        )
        return JsonResponse({'reply': reply})

    if any(word in text for word in ['hi', 'hello', 'namaste', 'help']):
        reply = (
            "Hello! I am here to help 😊\n\n"
            "You can ask me about:\n"
            "- Certificates\n"
            "- Bills and taxes\n"
            "- Complaints\n"
            "- Application tracking\n\n"
            "For exact status, share your GP or CMP number."
        )
        return JsonResponse({'reply': reply})

    reply = (
        "Sorry, I didn’t understand that.\n"
        "You can ask about certificates, bills, or complaints 😊"
    )

    return JsonResponse({'reply': reply})


@login_required
def activity_history(request):
    """User activity timeline view."""
    activities = UserActivity.objects.filter(user=request.user)
    paginator = Paginator(activities, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'portal_app/citizen/activity_history.html', {
        'title': 'Activity History',
        'page_obj': page_obj,
    })


@login_required
def download_center(request):
    """Unified download center for certificates and generated bill PDFs."""
    applications_with_docs = Application.objects.filter(
        applicant=request.user
    ).exclude(certificate_pdf='').order_by('-applied_date')

    recent_bill_docs = []

    for item in ElectricityBill.objects.filter(user=request.user).order_by('-generated_at')[:10]:
        recent_bill_docs.append({
            'title': f'Electricity Bill - {item.bill_month}',
            'reference': item.consumer_number,
            'url': reverse('download_service_bill_pdf', kwargs={'service_type': 'electricity', 'record_id': item.id}),
            'generated_at': item.generated_at,
        })

    for item in WaterBill.objects.filter(user=request.user).order_by('-generated_at')[:10]:
        recent_bill_docs.append({
            'title': f'Water Bill - {item.bill_month}',
            'reference': item.connection_number,
            'url': reverse('download_service_bill_pdf', kwargs={'service_type': 'water', 'record_id': item.id}),
            'generated_at': item.generated_at,
        })

    for item in PropertyTaxRecord.objects.filter(user=request.user).order_by('-created_at')[:10]:
        recent_bill_docs.append({
            'title': f'Property Tax - {item.tax_year}',
            'reference': item.property_number,
            'url': reverse('download_service_bill_pdf', kwargs={'service_type': 'property', 'record_id': item.id}),
            'generated_at': item.created_at,
        })

    recent_bill_docs = sorted(recent_bill_docs, key=lambda x: x['generated_at'], reverse=True)[:20]

    return render(request, 'portal_app/citizen/download_center.html', {
        'title': 'Download Center',
        'applications_with_docs': applications_with_docs,
        'recent_bill_docs': recent_bill_docs,
    })


@citizen_required
def pay_bills(request):
    """Unified bill payment page for pending electricity, water, and property records."""
    electricity_bills = ElectricityBill.objects.filter(
        user=request.user,
        payment_status__in=['pending', 'overdue']
    ).order_by('-generated_at')[:20]
    water_bills = WaterBill.objects.filter(
        user=request.user,
        payment_status__in=['pending', 'overdue']
    ).order_by('-generated_at')[:20]
    property_taxes = PropertyTaxRecord.objects.filter(
        user=request.user,
        payment_status__in=['pending', 'overdue']
    ).order_by('-created_at')[:20]

    context = {
        'title': 'Pay Bills',
        'electricity_bills': electricity_bills,
        'water_bills': water_bills,
        'property_taxes': property_taxes,
    }
    return render(request, 'portal_app/citizen/pay_bills.html', context)


@citizen_required
def payment_history(request):
    """Citizen payment history across tax and utility services."""
    tax_payments = TaxPayment.objects.filter(
        application__applicant=request.user,
        payment_status='paid'
    ).select_related('application').order_by('-payment_date')[:30]

    electricity_paid = ElectricityBill.objects.filter(
        user=request.user,
        payment_status='paid'
    ).order_by('-paid_at')[:30]

    water_paid = WaterBill.objects.filter(
        user=request.user,
        payment_status='paid'
    ).order_by('-paid_at')[:30]

    property_paid = PropertyTaxRecord.objects.filter(
        user=request.user,
        payment_status='paid'
    ).order_by('-paid_at')[:30]

    context = {
        'title': 'Payment History',
        'tax_payments': tax_payments,
        'electricity_paid': electricity_paid,
        'water_paid': water_paid,
        'property_paid': property_paid,
    }
    return render(request, 'portal_app/citizen/payment_history.html', context)


@login_required
def payments(request):
    """Payments landing page with direct access to payment workflows."""
    if request.user.role == 'admin':
        pending_electricity = ElectricityBill.objects.filter(payment_status__in=['pending', 'overdue']).count()
        pending_water = WaterBill.objects.filter(payment_status__in=['pending', 'overdue']).count()
        pending_property = PropertyTaxRecord.objects.filter(payment_status__in=['pending', 'overdue']).count()
        paid_total = TaxPayment.objects.filter(payment_status='paid').count()
    else:
        pending_electricity = ElectricityBill.objects.filter(
            user=request.user,
            payment_status__in=['pending', 'overdue']
        ).count()
        pending_water = WaterBill.objects.filter(
            user=request.user,
            payment_status__in=['pending', 'overdue']
        ).count()
        pending_property = PropertyTaxRecord.objects.filter(
            user=request.user,
            payment_status__in=['pending', 'overdue']
        ).count()
        paid_total = TaxPayment.objects.filter(
            application__applicant=request.user,
            payment_status='paid'
        ).count()

    context = {
        'title': 'Payments',
        'pending_electricity': pending_electricity,
        'pending_water': pending_water,
        'pending_property': pending_property,
        'paid_total': paid_total,
    }
    return render(request, 'portal_app/payments.html', context)


@login_required
def profile(request):
    """Profile overview panel with recent activity snapshot."""
    if request.user.role not in ['citizen', 'staff', 'admin']:
        return redirect('access_denied')

    recent_activities = UserActivity.objects.filter(user=request.user).order_by('-created_at')[:8]
    context = {
        'title': 'Profile',
        'recent_activities': recent_activities,
    }
    return render(request, 'portal_app/profile.html', context)


@login_required
def notifications_center(request):
    """Full notification center page."""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    paginator = Paginator(notifications, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'title': 'Notifications',
        'page_obj': page_obj,
    }
    return render(request, 'portal_app/citizen/notifications_center.html', context)


@admin_required
def admin_stats_api(request):
    """JSON data source for admin dashboard charts."""
    analytics = collect_admin_analytics()

    status_data = {
        'pending': Application.objects.filter(status='pending').count(),
        'under_review': Application.objects.filter(status='under_review').count(),
        'approved': Application.objects.filter(status='approved').count(),
        'rejected': Application.objects.filter(status='rejected').count(),
    }
    complaint_status = {
        'open': Complaint.objects.filter(status='open').count(),
        'in_progress': Complaint.objects.filter(status='in_progress').count(),
        'resolved': Complaint.objects.filter(status='resolved').count(),
        'closed': Complaint.objects.filter(status='closed').count(),
    }

    return JsonResponse({
        'generated_at': analytics['generated_at'].isoformat(),
        'overview': analytics['overview'],
        'trends': analytics['trends'],
        'charts': analytics['charts'],
        'insights': analytics['insights'],
        # Backward-compatible fields
        'status_data': status_data,
        'type_labels': analytics['charts']['certificate_distribution']['labels'],
        'type_totals': analytics['charts']['certificate_distribution']['values'],
        'complaint_status': complaint_status,
        'totals': {
            'users': analytics['overview']['total_users'],
            'applications': analytics['overview']['total_applications'],
            'approved': status_data['approved'],
            'rejected': status_data['rejected'],
        }
    })


# ============================================
# AUTHENTICATION VIEWS
# ============================================

def register_view(request):
    """Government-grade citizen registration with OTP verification before account creation."""
    if request.user.is_authenticated:
        # Redirect based on role if already logged in
        if request.user.role == 'admin':
            return redirect('admin_dashboard')
        elif request.user.role == 'staff':
            return redirect('staff_dashboard')
        else:
            return redirect('dashboard')
    
    if request.method == 'POST':
        form = CitizenRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                from .security_utils import generate_otp

                payload = form.get_pending_payload()
                email = payload['email']
                phone_number = payload['phone_number']
                username = payload['username']
                aadhar_number = payload.get('aadhar_number', '')

                # Hard duplicate checks before OTP initiation.
                if CustomUser.objects.filter(username__iexact=username).exists():
                    form.add_error('username', 'This username is already taken.')
                if CustomUser.objects.filter(email__iexact=email).exists():
                    form.add_error('email', 'This email is already registered.')
                if CustomUser.objects.filter(phone_number=phone_number).exists():
                    form.add_error('phone_number', 'This mobile number is already registered.')
                if aadhar_number and CustomUser.objects.filter(aadhar_number=aadhar_number).exists():
                    form.add_error('aadhar_number', 'This Aadhaar number is already registered.')

                if PendingRegistration.objects.filter(username__iexact=username, is_verified=False).exists():
                    form.add_error('username', 'This username is currently reserved. Please choose another one.')
                if PendingRegistration.objects.filter(email__iexact=email, is_verified=False).exists():
                    form.add_error('email', 'A pending registration already exists for this email.')

                if form.errors:
                    messages.error(request, 'Please correct the errors below.')
                    return render(request, 'portal_app/register.html', {'title': 'Register', 'form': form})

                # Remove stale in-progress registrations that conflict with the latest submission.
                PendingRegistration.objects.filter(
                    Q(email__iexact=email) | Q(phone_number=phone_number) | Q(username=username)
                ).delete()

                if aadhar_number:
                    PendingRegistration.objects.filter(aadhar_number=aadhar_number).delete()

                otp_code = generate_otp()
                pending_registration = PendingRegistration(
                    name=payload['name'],
                    first_name=payload['first_name'],
                    last_name=payload['last_name'],
                    username=username,
                    email=email,
                    phone_number=phone_number,
                    gender=payload['gender'],
                    date_of_birth=payload['date_of_birth'],
                    address=payload['address'],
                    state=payload['state'],
                    district=payload['district'],
                    pincode=payload['pincode'],
                    aadhar_number=aadhar_number,
                    profile_photo=payload.get('profile_photo'),
                )
                pending_registration.set_password(payload['raw_password'])
                pending_registration.set_otp(otp_code)
                pending_registration.save()
                _store_pending_registration_otp_session(request, otp_code)

                if not _send_registration_otp_email(pending_registration, otp_code):
                    pending_registration.delete()
                    messages.error(request, 'Unable to send OTP right now. Please try again in a moment.')
                    return render(request, 'portal_app/register.html', {'title': 'Register', 'form': form})

                _store_pending_registration_session(request, pending_registration)
                request.session.pop('pending_verification_user_id', None)

                messages.success(
                    request,
                    f'OTP has been sent to {pending_registration.email}. Verify OTP to complete registration.'
                )
                return redirect('register_verify_otp')
            
            except Exception:
                messages.error(request, 'An error occurred during registration. Please try again.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CitizenRegistrationForm()
    
    context = {
        'title': 'Register',
        'form': form,
    }
    return render(request, 'portal_app/register.html', context)


@require_http_methods(["GET", "POST"])
def register_multi_step_view(request):
    """Premium multi-step registration form with auto-save and profile preview."""
    if request.user.is_authenticated:
        # Redirect based on role if already logged in
        if request.user.role == 'admin':
            return redirect('admin_dashboard')
        elif request.user.role == 'staff':
            return redirect('staff_dashboard')
        else:
            return redirect('dashboard')

    if request.method == 'POST':
        try:
            from .security_utils import generate_otp

            # Extract form data from POST
            username = request.POST.get('username', '').strip()
            fullname = request.POST.get('fullname', '').strip()
            email = request.POST.get('email', '').strip().lower()
            mobile = request.POST.get('mobile', '').strip()
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')
            gender = request.POST.get('gender', '').strip()
            dob = request.POST.get('date_of_birth', '').strip()
            address = request.POST.get('address', '').strip()
            state = request.POST.get('state', '').strip()
            district = request.POST.get('district', '').strip()
            pincode = request.POST.get('pincode', '').strip()
            profile_photo = request.FILES.get('profile_photo')

            # Comprehensive validation
            errors = {}

            # Username validation
            if not username or not re.match(r'^[a-zA-Z0-9_]{4,20}$', username):
                errors['username'] = 'Username must be 4-20 characters (letters, numbers, underscore)'
            elif CustomUser.objects.filter(username__iexact=username).exists():
                errors['username'] = 'This username is already taken'
            elif PendingRegistration.objects.filter(username__iexact=username, is_verified=False).exists():
                errors['username'] = 'This username is reserved. Please choose another'

            # Full name validation
            if not fullname or len(fullname) < 2:
                errors['fullname'] = 'Full name is required (minimum 2 characters)'

            # Email validation
            if not email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                errors['email'] = 'Please enter a valid email address'
            elif CustomUser.objects.filter(email__iexact=email).exists():
                errors['email'] = 'This email is already registered'
            elif PendingRegistration.objects.filter(email__iexact=email, is_verified=False).exists():
                errors['email'] = 'A pending registration exists for this email'

            # Mobile validation
            if not mobile or not re.match(r'^[6-9]\d{9}$', mobile):
                errors['mobile'] = 'Mobile must be 10 digits starting with 6-9'
            elif CustomUser.objects.filter(phone_number=mobile).exists():
                errors['mobile'] = 'This mobile number is already registered'

            # Password validation
            if not password1 or len(password1) < 8:
                errors['password1'] = 'Password must be at least 8 characters'
            elif not (re.search(r'[A-Z]', password1) and re.search(r'[a-z]', password1) and re.search(r'\d', password1)):
                errors['password1'] = 'Password must include uppercase, lowercase, and number'

            if password1 != password2:
                errors['password2'] = 'Passwords do not match'

            # Gender validation
            if gender not in ['male', 'female', 'other']:
                errors['gender'] = 'Please select a valid gender'

            # Date of birth validation
            if dob:
                try:
                    birth_date = datetime.strptime(dob, '%Y-%m-%d').date()
                    age = (timezone.now().date() - birth_date).days // 365
                    if age < 18:
                        errors['dob'] = 'You must be at least 18 years old'
                except ValueError:
                    errors['dob'] = 'Invalid date format'
            else:
                errors['dob'] = 'Date of birth is required'

            # Address validation
            if not address or len(address) < 5:
                errors['address'] = 'Address is required (minimum 5 characters)'
            if not state or len(state) < 2:
                errors['state'] = 'State is required'
            if not district or len(district) < 2:
                errors['district'] = 'District is required'
            if not pincode or not re.match(r'^\d{6}$', pincode):
                errors['pincode'] = 'Pincode must be exactly 6 digits'

            # Profile photo validation
            if profile_photo:
                if profile_photo.size > 5 * 1024 * 1024:  # 5MB
                    errors['profile_photo'] = 'Image size must be less than 5MB'
                elif not profile_photo.content_type.startswith('image/'):
                    errors['profile_photo'] = 'Please upload a valid image file'

            # If there are validation errors, return them
            if errors:
                return JsonResponse({
                    'success': False,
                    'message': 'Validation failed',
                    'errors': errors
                }, status=400)

            # Clean up stale registrations
            PendingRegistration.objects.filter(
                Q(email__iexact=email) | Q(phone_number=mobile) | Q(username__iexact=username)
            ).delete()

            # Create pending registration
            otp_code = generate_otp()
            pending_registration = PendingRegistration(
                name=fullname,
                first_name=fullname.split()[0] if fullname else '',
                last_name=' '.join(fullname.split()[1:]) if len(fullname.split()) > 1 else '',
                username=username,
                email=email,
                phone_number=mobile,
                gender=gender,
                date_of_birth=dob,
                address=address,
                state=state,
                district=district,
                pincode=pincode,
                profile_photo=profile_photo,
            )
            pending_registration.set_password(password1)
            pending_registration.set_otp(otp_code)
            pending_registration.save()
            _store_pending_registration_otp_session(request, otp_code)

            # Send OTP email
            if not _send_registration_otp_email(pending_registration, otp_code):
                pending_registration.delete()
                return JsonResponse({
                    'success': False,
                    'message': 'Unable to send OTP right now. Please try again.'
                }, status=400)

            # Store session info
            _store_pending_registration_session(request, pending_registration)
            request.session.pop('pending_verification_user_id', None)

            return JsonResponse({
                'success': True,
                'message': 'OTP sent successfully',
                'redirect_url': reverse('register_verify_otp')
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': 'An error occurred during registration. Please try again.'
            }, status=500)
    
    # GET request - show the multi-step form template
    context = {
        'title': 'Premium Registration',
    }
    return render(request, 'portal_app/register-multi-step.html', context)


@require_http_methods(["GET", "POST"])
def register_verify_otp_view(request):
    """Verify registration OTP and create citizen account only after successful verification."""
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    pending = _get_pending_registration_from_session(request)

    if not pending:
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'No pending registration found.', 'redirect_url': reverse('register')}, status=400)
        messages.error(request, 'No pending registration found. Please fill the registration form again.')
        return redirect('register')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = _normalize_otp_code(form.cleaned_data.get('otp_code'))
            session_otp = _normalize_otp_code(request.session.get('pending_registration_otp'))

            print('Entered OTP:', otp_code)
            print('Session OTP:', session_otp)
            print('Pending registration ID:', pending.id)

            if len(otp_code) != PendingRegistration.OTP_LENGTH:
                if is_ajax:
                    return JsonResponse({'success': False, 'message': 'Please enter a valid 6-digit OTP.'}, status=400)
                messages.error(request, 'Please enter a valid 6-digit OTP.')
                return render(request, 'portal_app/otp-verification-premium.html', {
                    'title': 'Verify Registration OTP',
                    'form': form,
                    'email': pending.email,
                    'time_remaining': pending.get_time_remaining(),
                    'minutes': pending.get_time_remaining() // 60,
                    'seconds': pending.get_time_remaining() % 60,
                    'attempts_left': max(0, PendingRegistration.OTP_MAX_ATTEMPTS - pending.otp_attempts),
                    'otp_exists': True,
                    'resend_cooldown': 60,
                    'expiry_minutes': 10,
                })

            if pending.is_expired():
                if is_ajax:
                    return JsonResponse({'success': False, 'message': 'OTP expired. Please resend OTP.'}, status=400)
                messages.error(request, 'OTP expired. Please resend OTP.')
            elif pending.otp_attempts >= PendingRegistration.OTP_MAX_ATTEMPTS:
                if is_ajax:
                    return JsonResponse({'success': False, 'message': 'Maximum OTP attempts reached. Please resend OTP.'}, status=400)
                messages.error(request, 'Maximum OTP attempts reached. Please resend OTP.')
            elif session_otp and otp_code == session_otp:
                try:
                    with transaction.atomic():
                        if CustomUser.objects.filter(username__iexact=pending.username).exists():
                            raise ValueError('This username is already registered. Please choose another one and register again.')
                        if CustomUser.objects.filter(email__iexact=pending.email).exists():
                            raise ValueError('This email is already registered. Please login.')
                        if CustomUser.objects.filter(phone_number=pending.phone_number).exists():
                            raise ValueError('This mobile number is already registered. Please login.')
                        if pending.aadhar_number and CustomUser.objects.filter(aadhar_number=pending.aadhar_number).exists():
                            raise ValueError('This Aadhaar number is already registered. Please login.')

                        user = CustomUser(
                            name=pending.name,
                            first_name=pending.first_name,
                            last_name=pending.last_name,
                            username=pending.username,
                            email=pending.email,
                            role='citizen',
                            phone_number=pending.phone_number,
                            gender=pending.gender,
                            date_of_birth=pending.date_of_birth,
                            address=pending.address,
                            state=pending.state,
                            district=pending.district,
                            village=pending.district,
                            pincode=pending.pincode,
                            aadhar_number=pending.aadhar_number or None,
                            email_verified=True,
                            email_verified_at=timezone.now(),
                            is_active=True,
                        )
                        user.password = pending.password_hash
                        if pending.profile_photo:
                            user.profile_photo = pending.profile_photo
                        user.save()

                        pending.is_verified = True
                        pending.save(update_fields=['is_verified'])
                        pending.delete()

                    _clear_pending_registration_session(request)
                    success_message = 'Registration completed successfully. Your account is now active.'
                    if is_ajax:
                        return JsonResponse({'success': True, 'message': success_message, 'redirect_url': reverse('login')})
                    messages.success(request, success_message)
                    return redirect('login')
                except ValueError as validation_error:
                    if is_ajax:
                        return JsonResponse({'success': False, 'message': str(validation_error), 'redirect_url': reverse('login')}, status=400)
                    messages.error(request, str(validation_error))
                    return redirect('login')
                except Exception:
                    if is_ajax:
                        return JsonResponse({'success': False, 'message': 'Unable to complete registration. Please try again.'}, status=500)
                    messages.error(request, 'Unable to complete registration. Please try again.')
                    return redirect('register_verify_otp')
            elif pending.verify_otp(otp_code):
                try:
                    with transaction.atomic():
                        if CustomUser.objects.filter(username__iexact=pending.username).exists():
                            raise ValueError('This username is already registered. Please choose another one and register again.')
                        if CustomUser.objects.filter(email__iexact=pending.email).exists():
                            raise ValueError('This email is already registered. Please login.')
                        if CustomUser.objects.filter(phone_number=pending.phone_number).exists():
                            raise ValueError('This mobile number is already registered. Please login.')
                        if pending.aadhar_number and CustomUser.objects.filter(aadhar_number=pending.aadhar_number).exists():
                            raise ValueError('This Aadhaar number is already registered. Please login.')

                        user = CustomUser(
                            name=pending.name,
                            first_name=pending.first_name,
                            last_name=pending.last_name,
                            username=pending.username,
                            email=pending.email,
                            role='citizen',
                            phone_number=pending.phone_number,
                            gender=pending.gender,
                            date_of_birth=pending.date_of_birth,
                            address=pending.address,
                            state=pending.state,
                            district=pending.district,
                            village=pending.district,
                            pincode=pending.pincode,
                            aadhar_number=pending.aadhar_number or None,
                            email_verified=True,
                            email_verified_at=timezone.now(),
                            is_active=True,
                        )
                        user.password = pending.password_hash
                        if pending.profile_photo:
                            user.profile_photo = pending.profile_photo
                        user.save()

                        pending.is_verified = True
                        pending.save(update_fields=['is_verified'])
                        pending.delete()

                    _clear_pending_registration_session(request)
                    success_message = 'Registration completed successfully. Your account is now active.'
                    if is_ajax:
                        return JsonResponse({'success': True, 'message': success_message, 'redirect_url': reverse('login')})
                    messages.success(request, success_message)
                    return redirect('login')
                except ValueError as validation_error:
                    if is_ajax:
                        return JsonResponse({'success': False, 'message': str(validation_error), 'redirect_url': reverse('login')}, status=400)
                    messages.error(request, str(validation_error))
                    return redirect('login')
                except Exception:
                    if is_ajax:
                        return JsonResponse({'success': False, 'message': 'Unable to complete registration. Please try again.'}, status=500)
                    messages.error(request, 'Unable to complete registration. Please try again.')
                    return redirect('register_verify_otp')
            else:
                attempts_left = max(0, PendingRegistration.OTP_MAX_ATTEMPTS - pending.otp_attempts)
                error_message = f'Invalid OTP code. {attempts_left} attempt(s) remaining.'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message}, status=400)
                messages.error(request, error_message)
        else:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Please enter a valid 6-digit OTP.'}, status=400)
            messages.error(request, 'Please enter a valid 6-digit OTP.')
    else:
        form = OTPVerificationForm()

    time_remaining = pending.get_time_remaining()
    minutes = time_remaining // 60
    seconds = time_remaining % 60
    context = {
        'title': 'Verify Registration OTP',
        'form': form,
        'email': pending.email,
        'time_remaining': time_remaining,
        'minutes': minutes,
        'seconds': seconds,
        'attempts_left': max(0, PendingRegistration.OTP_MAX_ATTEMPTS - pending.otp_attempts),
        'otp_exists': True,
        'resend_cooldown': 60,
        'expiry_minutes': 10,
    }
    return render(request, 'portal_app/otp-verification-premium.html', context)


@require_POST
def register_resend_otp_view(request):
    """Resend registration OTP for pending citizen signups."""
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    pending = _get_pending_registration_from_session(request)

    if not pending:
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'No pending registration found.', 'redirect_url': reverse('register')}, status=400)
        messages.error(request, 'No pending registration found.')
        return redirect('register')

    cooldown_seconds = 60
    elapsed = int((timezone.now() - pending.last_otp_sent_at).total_seconds())
    if elapsed < cooldown_seconds:
        wait_for = cooldown_seconds - elapsed
        message = f'Please wait {wait_for} second(s) before requesting a new OTP.'
        if is_ajax:
            return JsonResponse({'success': False, 'message': message}, status=400)
        messages.error(request, message)
        return redirect('register_verify_otp')

    from .security_utils import generate_otp
    otp_code = generate_otp()
    pending.set_otp(otp_code)
    pending.save(update_fields=['otp_code_hash', 'otp_expires_at', 'otp_attempts', 'last_otp_sent_at', 'updated_at'])
    _store_pending_registration_otp_session(request, otp_code)

    if _send_registration_otp_email(pending, otp_code):
        success_message = f'New OTP sent to {pending.email}. It is valid for 10 minutes.'
        if is_ajax:
            return JsonResponse({'success': True, 'message': success_message, 'expiry_minutes': 10}, status=200)
        messages.success(request, success_message)
    else:
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'Unable to resend OTP right now. Please try again.'}, status=500)
        messages.error(request, 'Unable to resend OTP right now. Please try again.')

    return redirect('register_verify_otp')


def login_view(request):
    """
    User Login with Email Verification Check
    
    Security:
    - Checks if email is verified before allowing login
    - Redirects to OTP verification if email not verified
    - Role-based authentication and redirection
    """
    if request.user.is_authenticated:
        return _redirect_authenticated_user(request.user)
    
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
                if user.role not in ['citizen', 'staff', 'admin']:
                    messages.error(request, 'Invalid user role. Please contact support.')
                    return redirect('login')
                # Skip OTP verification for admin users
                if user.role != 'admin' and not user.email_verified:
                    messages.warning(
                        request,
                        'Your email is not verified. Please verify your email to login.'
                    )
                    # Store user ID for OTP verification
                    request.session['pending_verification_user_id'] = user.id
                    request.session['pending_user_id'] = user.id
                    request.session.modified = True
                    
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

                # Session persistence for login UX.
                remember_me = request.POST.get('remember_me') == 'on'
                if remember_me:
                    request.session.set_expiry(60 * 60 * 24 * 30)
                else:
                    request.session.set_expiry(0)

                messages.success(request, f'Welcome back, {user.first_name}!')
                
                # Role-based redirection
                log_user_activity(
                    user=user,
                    action='login',
                    description='Logged in to portal.',
                    reference=user.username
                )

                return _redirect_authenticated_user(user)
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


def admin_login_view(request):
    """
    Admin-only Login

    Security:
    - Only allows users with role=admin
    - OTP verification is not required for admins
    """
    if request.user.is_authenticated:
        return _redirect_authenticated_user(request.user)

    if request.method == 'POST':
        # Temporarily disabled rate limiting for testing
        # from .security_utils import check_rate_limit, rate_limit_exceeded_response

        username_input = request.POST.get('username', '').strip()
        client_ip = get_client_ip(request)
        
        # Temporarily disabled rate limiting
        # rate_limit_id = f"admin_login:{username_input}:{client_ip}"
        # if not check_rate_limit(rate_limit_id, limit=5, period=300):
        #     return rate_limit_exceeded_response()

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
                if user.role not in ['citizen', 'staff', 'admin']:
                    messages.error(request, 'Invalid user role. Please contact support.')
                    return redirect('admin_login')
                if user.role != 'admin':
                    messages.error(request, 'Only admins can login here.')
                    return redirect('admin_login')

                if not user.is_active:
                    messages.error(
                        request,
                        'Your account is pending approval. Please contact the administrator.'
                    )
                    return redirect('admin_login')

                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('admin_dashboard')
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
    return render(request, 'portal_app/admin_login.html', context)


def _handle_staff_form_submission(request, form, success_message):
    """Persist a staff form and invalidate active sessions when the account is disabled."""
    staff_user = form.save(commit=False)
    _sync_staff_user(staff_user, is_active=form.cleaned_data.get('is_active', True))
    staff_user.save()

    if not staff_user.is_active:
        _force_logout_user_ids([staff_user.id])

    log_user_activity(
        user=request.user,
        action='user_managed',
        description=f'Managed staff account for {staff_user.username}.',
        reference=staff_user.username,
    )
    messages.success(request, success_message.format(staff_user=staff_user))
    return redirect('staff_management')


@admin_required
def system_admin_panel(request):
    """
    System Admin Panel - Django Admin embedded in dashboard
    Only Admin can access this function
    """
    # Handle AJAX requests for dynamic loading
    if request.GET.get('ajax') == '1':
        template_name = 'portal_app/system_admin_panel_fixed.html'
    else:
        template_name = 'portal_app/system_admin_panel_fixed.html'
    
    context = {
        'title': 'System Administration',
    }
    return render(request, template_name, context)


@admin_required
def create_staff(request):
    """
    Admin-only view to create staff accounts
    Only Admin can access this function
    """
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            return _handle_staff_form_submission(
                request,
                form,
                'Staff account created successfully for {staff_user.username}.',
            )
    else:
        form = StaffCreationForm()

    context = {
        'title': 'Create Staff Account',
        'form': form,
    }
    return render(request, 'portal_app/admin/create_staff.html', context)


@staff_required
def staff_dashboard(request):
    """
    Staff Dashboard with limited permissions
    Staff can only view and process applications
    """
    # Application Statistics
    total_applications = Application.objects.count()
    pending_applications = Application.objects.filter(status='pending').count()
    under_review_applications = Application.objects.filter(status='under_review').count()
    approved_applications = Application.objects.filter(status='approved').count()
    rejected_applications = Application.objects.filter(status='rejected').count()
    recent_complaints = Complaint.objects.select_related('complainant').order_by('-filed_date')[:6]
    review_queue = Application.objects.select_related('applicant').filter(
        status__in=['pending', 'under_review']
    ).order_by('status', '-applied_date')[:10]
    
    # Recent Activity
    recent_applications = Application.objects.select_related(
        'applicant'
    ).order_by('-applied_date')[:10]
    
    complaints_count = Complaint.objects.count()
    recent_activities = UserActivity.objects.select_related('user').order_by('-created_at')[:8]
    top_category = (
        Application.objects.values('application_type')
        .annotate(total=Count('id'))
        .order_by('-total')
        .first()
    )
    top_category_label = top_category['application_type'].replace('_', ' ').title() if top_category else 'Income Certificate'

    context = {
        'title': 'Staff Dashboard',
        'dashboard_role': 'staff',
        'dashboard_heading': 'Staff Command Center',
        'dashboard_subtitle': 'Assigned work, pending queues, and live operational insights.',
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'under_review_applications': under_review_applications,
        'approved_applications': approved_applications,
        'rejected_applications': rejected_applications,
        'complaints_count': complaints_count,
        'extra_metric_label': 'Assigned Tasks',
        'extra_metric_value': pending_applications + under_review_applications,
        'review_queue': review_queue,
        'recent_applications': recent_applications,
        'recent_complaints': recent_complaints,
        'recent_activities': recent_activities,
        'insight_cards': _build_dashboard_insights(
            'staff',
            total_applications,
            pending_applications,
            approved_applications,
            rejected_applications,
            top_category_label,
        ),
    }
    return render(request, 'portal_app/dashboard/unified_home.html', context)


@admin_required
def admin_create_staff(request):
    """
    Create staff account from admin panel
    """
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            return _handle_staff_form_submission(
                request,
                form,
                'Staff account created successfully for {staff_user.username}.',
            )
        messages.error(request, 'Please correct the errors below.')
    else:
        form = StaffCreationForm()

    context = {
        'title': 'Create Staff Account',
        'form': form,
    }
    return render(request, 'portal_app/admin/create_staff.html', context)


@admin_required
def staff_management(request):
    """Admin-only staff management dashboard."""
    staff_queryset = CustomUser.objects.filter(is_staff=True, is_superuser=False).order_by('-created_at')

    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    if search_query:
        staff_queryset = staff_queryset.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )

    if status_filter == 'active':
        staff_queryset = staff_queryset.filter(is_active=True)
    elif status_filter == 'inactive':
        staff_queryset = staff_queryset.filter(is_active=False)

    paginator = Paginator(staff_queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': 'Staff Management',
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'staff_count': staff_queryset.count(),
        'active_staff_count': staff_queryset.filter(is_active=True).count(),
        'inactive_staff_count': staff_queryset.filter(is_active=False).count(),
    }
    return render(request, 'portal_app/admin/staff_management.html', context)


@admin_required
def admin_edit_staff(request, user_id):
    """Edit an existing staff account."""
    staff_user = get_object_or_404(CustomUser, pk=user_id, is_staff=True, is_superuser=False)

    if request.method == 'POST':
        form = StaffManagementForm(request.POST, request.FILES, instance=staff_user)
        if form.is_valid():
            updated_user = form.save(commit=False)
            _sync_staff_user(updated_user, is_active=form.cleaned_data.get('is_active', True))
            updated_user.save()
            messages.success(request, f'Staff account for {updated_user.username} updated successfully.')
            return redirect('staff_management')
    else:
        form = StaffManagementForm(instance=staff_user)

    context = {
        'title': 'Edit Staff Account',
        'form': form,
        'staff_user': staff_user,
        'mode': 'edit',
    }
    return render(request, 'portal_app/admin/staff_form.html', context)


@admin_required
@require_POST
def admin_toggle_staff_status(request, user_id):
    """Activate or deactivate a staff account."""
    staff_user = get_object_or_404(CustomUser, pk=user_id, is_staff=True, is_superuser=False)
    staff_user.is_active = not staff_user.is_active
    _sync_staff_user(staff_user, is_active=staff_user.is_active)
    staff_user.save(update_fields=['is_active', 'role', 'is_staff', 'is_superuser'])

    if not staff_user.is_active:
        _force_logout_user_ids([staff_user.id])

    state_label = 'activated' if staff_user.is_active else 'deactivated'
    messages.success(request, f'Staff account {staff_user.username} has been {state_label}.')
    return redirect('staff_management')


@admin_required
@require_POST
def admin_delete_staff(request, user_id):
    """Delete a staff account after invalidating active sessions."""
    staff_user = get_object_or_404(CustomUser, pk=user_id, is_staff=True, is_superuser=False)
    username = staff_user.username
    _force_logout_user_ids([staff_user.id])
    staff_user.delete()
    messages.success(request, f'Staff account {username} deleted successfully.')
    return redirect('staff_management')


@staff_required
@require_POST
def staff_application_action(request, application_id):
    """Fast staff workflow for approving or rejecting an application."""
    application = get_object_or_404(Application, pk=application_id)
    new_status = request.POST.get('action', '').strip().lower()

    if new_status not in {'approved', 'rejected'}:
        messages.error(request, 'Choose either approve or reject.')
        return redirect('staff_dashboard')

    old_status = application.status
    if old_status == new_status:
        messages.info(request, f'Application {application.application_number} is already {new_status}.')
        return redirect('staff_dashboard')

    application.status = new_status
    application.reviewed_by = request.user
    application.reviewed_date = timezone.now()
    application.admin_remarks = request.POST.get('admin_remarks', '').strip() or application.admin_remarks
    application.save(update_fields=['status', 'reviewed_by', 'reviewed_date', 'admin_remarks'])

    create_status_history(
        application=application,
        old_status=old_status,
        new_status=new_status,
        changed_by=request.user,
        remarks=application.admin_remarks,
    )

    log_user_activity(
        user=request.user,
        action=f'application_{new_status}',
        description=f'Changed {application.application_number} from {old_status} to {new_status}.',
        application=application,
        reference=application.application_number,
    )

    log_user_activity(
        user=application.applicant,
        action=f'application_{new_status}',
        description=f'Your application {application.application_number} was {new_status}.',
        application=application,
        reference=application.application_number,
    )

    create_notification(
        recipient=application.applicant,
        title='Application Status Updated',
        message=f'Application {application.application_number} is now {application.get_status_display()}.',
        category='application',
        target_url=reverse('application_detail', kwargs={'application_id': application.id}),
    )

    messages.success(request, f'Application {application.application_number} has been {new_status}.')
    return redirect('staff_dashboard')


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
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    if request.user.role == 'staff':
        return redirect('staff_dashboard')
    template_name = 'portal_app/dashboard/unified_home.html'
    
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
    complaints_qs = Complaint.objects.filter(complainant=request.user)
    complaints = complaints_qs[:5]
    complaint_counts = {
        'total': complaints_qs.count(),
        'open': complaints_qs.filter(status='open').count(),
        'in_progress': complaints_qs.filter(status='in_progress').count(),
        'resolved': complaints_qs.filter(status='resolved').count(),
    }
    
    context = {
        'title': 'Dashboard',
        'dashboard_role': 'citizen',
        'dashboard_heading': 'Citizen Service Dashboard',
        'dashboard_subtitle': 'Personal applications, bills, complaints, and quick services in one premium view.',
        'stats': stats,
        'total_applications': stats['total_applications'],
        'pending_applications': stats['pending'],
        'approved_applications': stats['approved'],
        'rejected_applications': stats['rejected'],
        'complaints_count': complaint_counts['total'],
        'extra_metric_label': 'My Bill Requests',
        'extra_metric_value': BillRequest.objects.filter(application__applicant=request.user).count(),
        'recent_applications': recent_applications,
        'complaints': complaints,
        'recent_complaints': complaints,
        'recent_activities': UserActivity.objects.filter(user=request.user).order_by('-created_at')[:8],
        'insight_cards': _build_dashboard_insights(
            'citizen',
            stats['total_applications'],
            stats['pending'],
            stats['approved'],
            stats['rejected'],
            'Income Certificate',
        ),
        'complaint_counts': complaint_counts,
    }
    return render(request, template_name, context)


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

            log_user_activity(
                user=request.user,
                action='application_submitted',
                description=f'Birth certificate application submitted ({application.application_number}).',
                application=application,
                reference=application.application_number
            )

            create_notification(
                recipient=request.user,
                title='Application Submitted',
                message=f'Birth certificate request {application.application_number} submitted successfully.',
                category='application',
                target_url=reverse('application_detail', kwargs={'application_id': application.id})
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

            log_user_activity(
                user=request.user,
                action='application_submitted',
                description=f'Death certificate application submitted ({application.application_number}).',
                application=application,
                reference=application.application_number
            )

            create_notification(
                recipient=request.user,
                title='Application Submitted',
                message=f'Death certificate request {application.application_number} submitted successfully.',
                category='application',
                target_url=reverse('application_detail', kwargs={'application_id': application.id})
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

            log_user_activity(
                user=request.user,
                action='application_submitted',
                description=f'Income certificate application submitted ({application.application_number}).',
                application=application,
                reference=application.application_number
            )

            create_notification(
                recipient=request.user,
                title='Application Submitted',
                message=f'Income certificate request {application.application_number} submitted successfully.',
                category='application',
                target_url=reverse('application_detail', kwargs={'application_id': application.id})
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

            log_user_activity(
                user=request.user,
                action='payment_recorded',
                description=f'{tax_type.replace("_", " ").title()} payment application submitted ({application.application_number}).',
                application=application,
                reference=application.application_number
            )

            create_notification(
                recipient=request.user,
                title='Payment Application Submitted',
                message=f'Tax/payment application {application.application_number} submitted for review.',
                category='bill',
                target_url=reverse('application_detail', kwargs={'application_id': application.id})
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
            application = Application.objects.create(
                applicant=request.user,
                application_type='complaint_submission',
                status='pending'
            )

            complaint = form.save(commit=False)
            complaint.complainant = request.user
            complaint.application = application
            complaint.save()

            create_status_history(
                application=application,
                old_status='',
                new_status='pending',
                changed_by=request.user,
                remarks=f'Complaint submitted: {complaint.subject}'
            )
            
            # Create complaint history
            ComplaintHistory.objects.create(
                complaint=complaint,
                action='created',
                new_value=complaint.get_status_display(),
                performed_by=request.user,
                notes=f'Complaint filed: {complaint.subject}'
            )

            log_user_activity(
                user=request.user,
                action='complaint_submitted',
                description=f'Complaint filed ({complaint.complaint_number}) - {complaint.subject}',
                application=application,
                reference=complaint.complaint_number
            )

            create_notification(
                recipient=request.user,
                title='Complaint Registered',
                message=f'Complaint {complaint.complaint_number} submitted and pending review.',
                category='complaint',
                target_url=reverse('complaint_detail', kwargs={'complaint_id': complaint.id})
            )
            
            messages.success(
                request,
                f'<strong>Complaint filed successfully!</strong><br>'
                f'Complaint Number: <strong>{complaint.complaint_number}</strong><br>'
                f'Application Number: <strong>{application.application_number}</strong><br>'
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


@login_required
@citizen_required
def electricity_bill_service(request):
    """Electricity bill module: search/fetch bill and mark as paid."""
    today = timezone.localdate()
    ElectricityBill.objects.filter(user=request.user, payment_status='pending', due_date__lt=today).update(payment_status='overdue')
    bills = ElectricityBill.objects.filter(user=request.user).order_by('-generated_at')
    lookup_form = ElectricityBillLookupForm(request.POST or None)

    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    if search_query:
        bills = bills.filter(consumer_number__icontains=search_query)
    if status_filter:
        bills = bills.filter(payment_status=status_filter)

    if request.method == 'POST':
        action = request.POST.get('action', 'fetch')

        if action == 'fetch':
            if lookup_form.is_valid():
                consumer_number = lookup_form.cleaned_data['consumer_number']
                month_key = timezone.now().strftime('%Y-%m')
                due_date = (timezone.now() + timedelta(days=15)).date()
                demo_amount = _build_demo_amount(consumer_number, 350.0)

                bill, created = ElectricityBill.objects.get_or_create(
                    user=request.user,
                    consumer_number=consumer_number,
                    bill_month=month_key,
                    defaults={
                        'amount': demo_amount,
                        'due_date': due_date,
                        'payment_status': 'pending',
                    }
                )
                if created:
                    messages.success(request, f'Bill fetched successfully for consumer number {consumer_number}.')
                else:
                    messages.info(request, f'Bill already available for consumer number {consumer_number}.')
            else:
                messages.error(request, 'Please enter a valid consumer number.')

        elif action == 'pay':
            bill_id = request.POST.get('bill_id')
            bill = get_object_or_404(ElectricityBill, id=bill_id, user=request.user)
            if bill.payment_status == 'paid':
                messages.info(request, 'This electricity bill is already paid.')
            else:
                bill.payment_status = 'paid'
                bill.paid_at = timezone.now()
                bill.transaction_id = f"ELEC{timezone.now().strftime('%Y%m%d%H%M%S')}"
                bill.save(update_fields=['payment_status', 'paid_at', 'transaction_id'])
                messages.success(request, f'Payment successful. Transaction ID: {bill.transaction_id}')

        elif action == 'delete':
            bill_id = request.POST.get('bill_id')
            bill = get_object_or_404(ElectricityBill, id=bill_id, user=request.user)
            if bill.payment_status == 'paid':
                messages.error(request, 'Paid bills cannot be deleted.')
            else:
                bill.delete()
                messages.success(request, 'Electricity bill removed successfully.')

        return redirect('electricity_bill_service')

    context = {
        'title': 'Electricity Bill Service',
        'lookup_form': lookup_form,
        'bills': bills,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'portal_app/citizen/electricity_bill_service.html', context)


@login_required
@citizen_required
def water_bill_service(request):
    """Water bill module: search/fetch bill and mark as paid."""
    today = timezone.localdate()
    WaterBill.objects.filter(user=request.user, payment_status='pending', due_date__lt=today).update(payment_status='overdue')
    bills = WaterBill.objects.filter(user=request.user).order_by('-generated_at')
    lookup_form = WaterBillLookupForm(request.POST or None)

    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    if search_query:
        bills = bills.filter(connection_number__icontains=search_query)
    if status_filter:
        bills = bills.filter(payment_status=status_filter)

    if request.method == 'POST':
        action = request.POST.get('action', 'fetch')

        if action == 'fetch':
            if lookup_form.is_valid():
                connection_number = lookup_form.cleaned_data['connection_number']
                month_key = timezone.now().strftime('%Y-%m')
                due_date = (timezone.now() + timedelta(days=15)).date()
                demo_amount = _build_demo_amount(connection_number, 180.0)

                bill, created = WaterBill.objects.get_or_create(
                    user=request.user,
                    connection_number=connection_number,
                    bill_month=month_key,
                    defaults={
                        'amount': demo_amount,
                        'due_date': due_date,
                        'payment_status': 'pending',
                    }
                )
                if created:
                    messages.success(request, f'Bill fetched successfully for connection number {connection_number}.')
                else:
                    messages.info(request, f'Bill already available for connection number {connection_number}.')
            else:
                messages.error(request, 'Please enter a valid water connection number.')

        elif action == 'pay':
            bill_id = request.POST.get('bill_id')
            bill = get_object_or_404(WaterBill, id=bill_id, user=request.user)
            if bill.payment_status == 'paid':
                messages.info(request, 'This water bill is already paid.')
            else:
                bill.payment_status = 'paid'
                bill.paid_at = timezone.now()
                bill.transaction_id = f"WATR{timezone.now().strftime('%Y%m%d%H%M%S')}"
                bill.save(update_fields=['payment_status', 'paid_at', 'transaction_id'])
                messages.success(request, f'Payment successful. Transaction ID: {bill.transaction_id}')

        elif action == 'delete':
            bill_id = request.POST.get('bill_id')
            bill = get_object_or_404(WaterBill, id=bill_id, user=request.user)
            if bill.payment_status == 'paid':
                messages.error(request, 'Paid bills cannot be deleted.')
            else:
                bill.delete()
                messages.success(request, 'Water bill removed successfully.')

        return redirect('water_bill_service')

    context = {
        'title': 'Water Bill Service',
        'lookup_form': lookup_form,
        'bills': bills,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'portal_app/citizen/water_bill_service.html', context)


@login_required
@citizen_required
def property_tax_service(request):
    """Property/House tax module with basic tax calculation and payment tracking."""
    today = timezone.localdate()
    PropertyTaxRecord.objects.filter(user=request.user, payment_status='pending', due_date__lt=today).update(payment_status='overdue')
    records = PropertyTaxRecord.objects.filter(user=request.user).order_by('-created_at')
    form = PropertyTaxRecordForm(request.POST or None)

    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    if search_query:
        records = records.filter(Q(property_number__icontains=search_query) | Q(owner_name__icontains=search_query))
    if status_filter:
        records = records.filter(payment_status=status_filter)

    if request.method == 'POST':
        action = request.POST.get('action', 'create')

        if action == 'create':
            if form.is_valid():
                tax_record = form.save(commit=False)
                tax_record.user = request.user
                tax_record.save()
                messages.success(request, f'Property tax record created. Amount due: Rs. {tax_record.tax_amount}')
                return redirect('property_tax_service')
            messages.error(request, 'Please correct the highlighted errors in property tax form.')

        elif action == 'pay':
            record_id = request.POST.get('record_id')
            record = get_object_or_404(PropertyTaxRecord, id=record_id, user=request.user)
            if record.payment_status == 'paid':
                messages.info(request, 'This property tax entry is already paid.')
            else:
                record.payment_status = 'paid'
                record.paid_at = timezone.now()
                record.transaction_id = f"PROP{timezone.now().strftime('%Y%m%d%H%M%S')}"
                record.save(update_fields=['payment_status', 'paid_at', 'transaction_id'])
                messages.success(request, f'Property tax paid successfully. Transaction ID: {record.transaction_id}')
            return redirect('property_tax_service')

        elif action == 'delete':
            record_id = request.POST.get('record_id')
            record = get_object_or_404(PropertyTaxRecord, id=record_id, user=request.user)
            if record.payment_status == 'paid':
                messages.error(request, 'Paid tax records cannot be deleted.')
            else:
                record.delete()
                messages.success(request, 'Property tax record deleted successfully.')
            return redirect('property_tax_service')

    context = {
        'title': 'Property Tax Service',
        'form': form,
        'records': records,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'portal_app/citizen/property_tax_service.html', context)


@login_required
@citizen_required
def submit_bill_request(request):
    """Submit a bill-related application request for admin approval."""
    if request.method == 'POST':
        form = BillRequestForm(request.POST, request.FILES)
        if form.is_valid():
            application = Application.objects.create(
                applicant=request.user,
                application_type='bill_request',
                status='pending'
            )

            bill_request = form.save(commit=False)
            bill_request.application = application
            bill_request.save()

            create_status_history(
                application=application,
                old_status='',
                new_status='pending',
                changed_by=request.user,
                remarks=f'Bill request submitted: {bill_request.subject}'
            )

            log_user_activity(
                user=request.user,
                action='application_submitted',
                description=f'Bill request submitted ({application.application_number}) - {bill_request.subject}',
                application=application,
                reference=application.application_number
            )

            create_notification(
                recipient=request.user,
                title='Bill Request Submitted',
                message=f'Bill request {application.application_number} submitted successfully.',
                category='bill',
                target_url=reverse('application_detail', kwargs={'application_id': application.id})
            )

            messages.success(
                request,
                f'Bill request submitted successfully. Application Number: {application.application_number}'
            )
            return redirect('application_detail', application_id=application.id)
    else:
        form = BillRequestForm()

    context = {
        'title': 'Bill Related Request',
        'form': form,
    }
    return render(request, 'portal_app/citizen/submit_bill_request.html', context)


@login_required
@citizen_required
def download_service_bill_pdf(request, service_type, record_id):
    """Basic PDF download for bill/tax receipts."""
    service_type = service_type.lower()

    if service_type == 'electricity':
        record = get_object_or_404(ElectricityBill, id=record_id, user=request.user)
        title = 'Electricity Bill'
        ref_no = record.consumer_number
        period = record.bill_month
        amount = record.amount
        due_date = record.due_date
        status = record.get_payment_status_display()
        transaction_id = record.transaction_id or 'N/A'
    elif service_type == 'water':
        record = get_object_or_404(WaterBill, id=record_id, user=request.user)
        title = 'Water Bill'
        ref_no = record.connection_number
        period = record.bill_month
        amount = record.amount
        due_date = record.due_date
        status = record.get_payment_status_display()
        transaction_id = record.transaction_id or 'N/A'
    elif service_type == 'property':
        record = get_object_or_404(PropertyTaxRecord, id=record_id, user=request.user)
        title = 'Property Tax Receipt'
        ref_no = record.property_number
        period = record.tax_year
        amount = record.tax_amount
        due_date = record.due_date
        status = record.get_payment_status_display()
        transaction_id = record.transaction_id or 'N/A'
    else:
        raise Http404('Invalid service type')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{service_type}_bill_{record_id}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    p.setTitle(f'{title} - {request.user.username}')

    y = 800
    p.setFont('Helvetica-Bold', 16)
    p.drawString(50, y, 'Digital Gram Panchayat Portal')
    y -= 30
    p.setFont('Helvetica-Bold', 13)
    p.drawString(50, y, title)
    y -= 30

    p.setFont('Helvetica', 11)
    lines = [
        f'Citizen: {request.user.get_full_name() or request.user.username}',
        f'Reference Number: {ref_no}',
        f'Billing Period/Year: {period}',
        f'Amount: Rs. {amount}',
        f'Due Date: {due_date}',
        f'Payment Status: {status}',
        f'Transaction ID: {transaction_id}',
        f'Generated At: {timezone.now().strftime("%d-%m-%Y %H:%M")}',
    ]

    for line in lines:
        p.drawString(50, y, line)
        y -= 20

    p.showPage()
    p.save()

    log_user_activity(
        user=request.user,
        action='document_downloaded',
        description=f'Downloaded {title} PDF ({ref_no}).',
        reference=f'{service_type}:{record_id}'
    )

    return response


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
def my_certificates(request):
    """Show application status and certificate availability in one place."""
    applications = Application.objects.filter(applicant=request.user).order_by('-applied_date')
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)

    paginator = Paginator(applications, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'title': 'My Certificates',
        'page_obj': page_obj,
        'status_filter': status_filter,
    }
    return render(request, 'portal_app/citizen/my_certificates.html', context)


@login_required
def application_detail(request, application_id):
    """
    View application details
    """
    # Admin/staff can inspect any application; citizens can only inspect their own.
    if request.user.role in ['admin', 'staff']:
        application = Application.objects.filter(pk=application_id).first()
        missing_redirect = 'admin_applications'
    else:
        application = Application.objects.filter(pk=application_id, applicant=request.user).first()
        missing_redirect = 'my_applications'

    if not application:
        messages.warning(request, 'The requested application was not found or is no longer available.')
        return redirect(missing_redirect)
    
    # Get specific certificate details
    certificate_data = None
    if application.application_type == 'birth_certificate':
        certificate_data = getattr(application, 'birth_certificate', None)
    elif application.application_type == 'death_certificate':
        certificate_data = getattr(application, 'death_certificate', None)
    elif application.application_type == 'income_certificate':
        certificate_data = getattr(application, 'income_certificate', None)
    elif application.application_type == 'complaint_submission' and hasattr(application, 'complaint_record'):
        certificate_data = application.complaint_record
    elif application.application_type == 'bill_request' and hasattr(application, 'bill_request'):
        certificate_data = application.bill_request
    elif application.application_type in ['water_tax', 'house_tax']:
        certificate_data = getattr(application, 'tax_payment', None)
    
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

@admin_required
def admin_dashboard(request):
    """
    Government-Style Admin Dashboard with comprehensive statistics
    Admin only - access controlled by role check
    """
    # Check if user is admin, if not redirect to admin_login
    if request.user.role != 'admin':
        return redirect('admin_login')
    
    template_name = 'portal_app/dashboard/unified_home.html'
    
    # Get real statistics
    from django.utils import timezone
    today = timezone.now().date()
    
    total_citizens = CustomUser.objects.filter(role='citizen').count()
    total_staff = CustomUser.objects.filter(role='staff').count()
    total_admins = CustomUser.objects.filter(role='admin').count()
    total_users = CustomUser.objects.count()
    new_users_today = CustomUser.objects.filter(date_joined__date=today).count()
    inactive_users = CustomUser.objects.filter(is_active=False).count()
    pending_applications = Application.objects.filter(status='pending').count()
    approved_applications = Application.objects.filter(status='approved').count()
    rejected_applications = Application.objects.filter(status='rejected').count()
    open_complaints = Complaint.objects.filter(status='open').count()
    total_complaints = Complaint.objects.count()
    applications_today = Application.objects.filter(applied_date__date=today).count()
    recent_applications = Application.objects.select_related('applicant').all().order_by('-applied_date')[:8]
    recent_complaints = Complaint.objects.select_related('complainant').all().order_by('-filed_date')[:6]
    recent_activities = UserActivity.objects.select_related('user').order_by('-created_at')[:8]

    top_category = (
        Application.objects.values('application_type')
        .annotate(total=Count('id'))
        .order_by('-total')
        .first()
    )
    top_category_label = top_category['application_type'].replace('_', ' ').title() if top_category else 'Income Certificate'

    analytics = collect_admin_analytics()
    
    context = {
        'title': 'Admin Dashboard',
        'dashboard_role': 'admin',
        'dashboard_heading': 'Admin Analytics Hub',
        'dashboard_subtitle': 'Full-stack analytics across users, applications, complaints, and operational growth.',
        'total_citizens': total_citizens,
        'total_staff': total_staff,
        'total_admins': total_admins,
        'total_users': total_users,
        'new_users_today': new_users_today,
        'inactive_users': inactive_users,
        'applications_today': applications_today,
        'total_applications': Application.objects.count(),
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'rejected_applications': rejected_applications,
        'complaints_count': total_complaints,
        'extra_metric_label': 'Total Users',
        'extra_metric_value': total_users,
        'recent_complaints_count': open_complaints,
        'recent_applications': recent_applications,
        'recent_complaints': recent_complaints,
        'recent_activities': recent_activities,
        'insight_cards': _build_dashboard_insights(
            'admin',
            Application.objects.count(),
            pending_applications,
            approved_applications,
            rejected_applications,
            top_category_label,
        ),
        'analytics': analytics,
        'can_send_reports': bool(request.user.email),
    }
    
    return render(request, template_name, context)


@admin_required
def admin_users(request):
    """Admin users management with search, filters, and pagination."""
    users = CustomUser.objects.all().order_by('-created_at')

    search_query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()
    status_filter = request.GET.get('status', '').strip()

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )

    if role_filter in ['admin', 'staff', 'citizen']:
        users = users.filter(role=role_filter)

    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)

    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': 'Manage Users',
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
    }
    return render(request, 'portal_app/admin/users.html', context)


@admin_required
@require_http_methods(["GET", "POST"])
def admin_edit_user(request, user_id):
    """Edit a citizen, staff member, or non-protected admin account."""
    user_obj = get_object_or_404(CustomUser, pk=user_id)

    if request.user.pk == user_obj.pk:
        messages.info(request, 'Use account settings to edit your own profile.')
        return redirect('settings')

    if request.method == 'POST':
        form = AdminUserForm(request.POST, request.FILES, instance=user_obj)
        if form.is_valid():
            edited_user = form.save()

            if not edited_user.is_active:
                _force_logout_user_ids([edited_user.id])

            log_user_activity(
                user=request.user,
                action='user_managed',
                description=f'Edited user account {edited_user.username}.',
                reference=edited_user.username,
            )
            messages.success(request, f'User {edited_user.username} updated successfully.')
            return redirect('admin_users')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminUserForm(instance=user_obj)

    context = {
        'title': 'Edit User',
        'form': form,
        'managed_user': user_obj,
    }
    return render(request, 'portal_app/admin/user_form.html', context)


@admin_required
@require_POST
def admin_delete_user(request, user_id):
    """Delete a non-protected user account."""
    user_obj = get_object_or_404(CustomUser, pk=user_id)

    if _is_protected_main_admin(user_obj) or request.user.pk == user_obj.pk:
        messages.error(request, 'This account is protected and cannot be deleted.')
        return redirect('admin_users')

    username = user_obj.username
    _force_logout_user_ids([user_obj.id])
    user_obj.delete()

    log_user_activity(
        user=request.user,
        action='user_managed',
        description=f'Deleted user account {username}.',
        reference=username,
    )
    messages.success(request, f'User {username} deleted successfully.')
    return redirect('admin_users')


@admin_required
def admin_reports(request):
    """Reports center for summary analytics and report actions."""
    analytics = collect_admin_analytics()
    context = {
        'title': 'Reports Center',
        'analytics': analytics,
    }
    return render(request, 'portal_app/admin/reports.html', context)


@admin_required
@require_POST
def trigger_admin_report(request):
    """Manual report trigger endpoint for admin users."""
    period = request.POST.get('period', 'daily').strip().lower()
    if period not in ['daily', 'weekly']:
        period = 'daily'

    sender = request.user.get_full_name() or request.user.username
    ok, msg = send_admin_report_email(period=period, triggered_by=sender)

    if ok:
        messages.success(request, msg)
    else:
        messages.error(request, f'Report sending failed: {msg}')

    return redirect(request.META.get('HTTP_REFERER') or reverse('admin_reports'))


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
    category_filter = request.GET.get('category', '').strip().lower()
    search_query = request.GET.get('q', '').strip()

    if category_filter == 'certificates':
        applications = applications.filter(application_type__in=CERTIFICATE_TYPES)
    elif category_filter == 'bills':
        applications = applications.filter(application_type__in=BILL_TYPES)
    
    if status_filter:
        applications = applications.filter(status=status_filter)
    if type_filter:
        applications = applications.filter(application_type=type_filter)
    if search_query:
        applications = applications.filter(
            Q(application_number__icontains=search_query) |
            Q(applicant__username__icontains=search_query) |
            Q(applicant__first_name__icontains=search_query) |
            Q(applicant__last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(applications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Manage Applications',
        'page_obj': page_obj,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'category_filter': category_filter,
        'search_query': search_query,
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
    elif application.application_type == 'complaint_submission' and hasattr(application, 'complaint_record'):
        certificate_data = application.complaint_record
    elif application.application_type == 'bill_request' and hasattr(application, 'bill_request'):
        certificate_data = application.bill_request
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

                log_user_activity(
                    user=request.user,
                    action=(
                        'application_approved' if updated_app.status == 'approved'
                        else 'application_rejected' if updated_app.status == 'rejected'
                        else 'application_updated'
                    ),
                    description=(
                        f'Updated {updated_app.application_number} status '
                        f'from {old_status or "new"} to {updated_app.status}.'
                    ),
                    application=updated_app,
                    reference=updated_app.application_number
                )

                applicant_activity_action = (
                    'application_approved' if updated_app.status == 'approved' else
                    'application_rejected' if updated_app.status == 'rejected' else
                    'application_updated'
                )
                log_user_activity(
                    user=updated_app.applicant,
                    action=applicant_activity_action,
                    description=(
                        f'Application {updated_app.application_number} status changed to '
                        f'{updated_app.get_status_display()}.'
                    ),
                    application=updated_app,
                    reference=updated_app.application_number
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

                    # Generate and save PDF in media folder
                    _save_application_pdf(updated_app)

                    # Send approval email with PDF attachment
                    email_sent, error_message = _send_approval_email_with_pdf(updated_app)
                    if email_sent:
                        updated_app.email_delivery_status = 'sent'
                        updated_app.approval_email_sent_at = timezone.now()
                        updated_app.email_delivery_error = ''
                        messages.success(
                            request,
                            f'Approval email with PDF sent to {updated_app.applicant.email}.'
                        )
                    else:
                        updated_app.email_delivery_status = 'failed'
                        updated_app.email_delivery_error = error_message
                        messages.warning(
                            request,
                            f'Application approved, but email delivery failed: {error_message}'
                        )
                    updated_app.save(update_fields=['certificate_pdf', 'email_delivery_status', 'approval_email_sent_at', 'email_delivery_error'])
                
                status_msg = 'approved' if updated_app.status == 'approved' else updated_app.status

                create_notification(
                    recipient=updated_app.applicant,
                    title='Application Status Updated',
                    message=(
                        f'Application {updated_app.application_number} is now '
                        f'{updated_app.get_status_display()}.'
                    ),
                    category='application',
                    target_url=reverse('application_detail', kwargs={'application_id': updated_app.id})
                )

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


@admin_required
def delete_application(request, id):
    """
    Delete an application (Admin only)
    POST request required for security
    """
    if request.method == "POST":
        application = get_object_or_404(Application, id=id)
        app_number = application.application_number
        application.delete()
        messages.success(request, f"Application {app_number} deleted successfully.")
    else:
        messages.error(request, "Invalid request method. Use POST to delete.")
    return redirect('admin_applications')


@staff_or_admin_required
def export_applications(request):
    """
    Export all applications to CSV file
    Available to staff and admin users
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="applications_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Application No', 'Applicant Name', 'Phone', 'Type', 'Status', 'Applied Date', 'Reviewed By', 'Review Date'])
    
    # Get all applications with related data
    applications = Application.objects.select_related('applicant', 'reviewed_by').all().order_by('-applied_date')
    
    for app in applications:
        writer.writerow([
            app.application_number,
            app.applicant.get_full_name(),
            app.applicant.phone_number,
            app.get_application_type_display(),
            app.get_status_display(),
            app.applied_date.strftime('%Y-%m-%d %H:%M:%S'),
            app.reviewed_by.get_full_name() if app.reviewed_by else 'Not Reviewed',
            app.reviewed_date.strftime('%Y-%m-%d %H:%M:%S') if app.reviewed_date else 'N/A',
        ])
    
    return response


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
    search_query = request.GET.get('q', '').strip()
    
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
    if search_query:
        complaints = complaints.filter(
            Q(complaint_number__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(complainant__username__icontains=search_query)
        )
    
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
        'search_query': search_query,
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

            log_user_activity(
                user=request.user,
                action='complaint_updated',
                description=(
                    f'Complaint {updated_complaint.complaint_number} updated to '
                    f'{updated_complaint.get_status_display()}.'
                ),
                application=updated_complaint.application,
                reference=updated_complaint.complaint_number
            )

            log_user_activity(
                user=updated_complaint.complainant,
                action='complaint_updated',
                description=(
                    f'Complaint {updated_complaint.complaint_number} status is now '
                    f'{updated_complaint.get_status_display()}.'
                ),
                application=updated_complaint.application,
                reference=updated_complaint.complaint_number
            )

            create_notification(
                recipient=updated_complaint.complainant,
                title='Complaint Status Updated',
                message=(
                    f'Complaint {updated_complaint.complaint_number} is now '
                    f'{updated_complaint.get_status_display()}.'
                ),
                category='complaint',
                target_url=reverse('complaint_detail', kwargs={'complaint_id': updated_complaint.id})
            )
            
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

def generate_marathi_certificate(request, application):
    """
    Generate Marathi certificate using enhanced ReportLab with proper formatting
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                         leftMargin=2*cm, rightMargin=2*cm,
                         topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    # Try to register Marathi-compatible font
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        # Try to use a system font that supports Marathi
        marathi_fonts = ['Noto Sans Devanagari', 'Mangal', 'Shivaji', 'Arial Unicode MS']
        font_registered = False
        
        for font_name in marathi_fonts:
            try:
                # Try to register the font
                pdfmetrics.registerFont(TTFont('MarathiFont', font_name))
                font_registered = True
                break
            except:
                continue
        
        if not font_registered:
            # Fallback to default but with warning
            font_name = 'Helvetica'
        else:
            font_name = 'MarathiFont'
            
    except Exception as e:
        font_name = 'Helvetica'
    
    # Custom Marathi-friendly styles
    title_style = ParagraphStyle(
        'MarathiTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.black,
        spaceAfter=20,
        alignment=1,  # Center
        fontName=font_name,
        wordWrap='CJK'
    )
    
    header_style = ParagraphStyle(
        'MarathiHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.black,
        spaceAfter=10,
        alignment=1,  # Center
        fontName=font_name,
        wordWrap='CJK'
    )
    
    normal_style = ParagraphStyle(
        'MarathiNormal',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.black,
        spaceAfter=8,
        alignment=0,  # Left/Justify
        fontName=font_name,
        leading=16,
        wordWrap='CJK'
    )
    
    label_style = ParagraphStyle(
        'MarathiLabel',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.black,
        fontName=font_name,
        wordWrap='CJK'
    )
    
    # Maharashtra Government Header
    elements.append(Paragraph("महाराष्ट्र शासन", title_style))
    elements.append(Paragraph("जिल्हा: पुणे", header_style))
    elements.append(Paragraph("तालुका: हवेली", header_style))
    elements.append(Paragraph("ग्रामपंचायत: मॉडेल ग्रामपंचायत", header_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Determine certificate type and content
    if application.application_type == 'birth_certificate':
        cert = application.birth_certificate
        
        elements.append(Paragraph("जन्म प्रमाणपत्र", title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Certificate body text
        cert_text = f"""
        ही प्रमाणित करण्यात येते की, खालील माहिती प्रमाणे जन्म नोंदविण्यात आला आहे.<br/>
        श्री./श्रीमती <b>{cert.child_name}</b> यांचा जन्म <b>{cert.date_of_birth.strftime('%d/%m/%Y')}</b> 
        रोजी <b>{cert.place_of_birth}</b> येथे झाला आहे.<br/><br/>
        बालकाचे लिंग <b>{cert.get_child_gender_display()}</b> असून वडील <b>{cert.father_name}</b> 
        आणि आई <b>{cert.mother_name}</b> यांच्या पोटी जन्म झाला आहे.
        """
        elements.append(Paragraph(cert_text, normal_style))
        
        # Details section
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("प्रमाणपत्र तपशील:", label_style))
        elements.append(Spacer(1, 0.2*cm))
        
        details = [
            ['प्रमाणपत्र क्रमांक:', cert.certificate_number or 'N/A'],
            ['दिनांक:', cert.issued_date.strftime('%d/%m/%Y') if cert.issued_date else 'N/A'],
            ['बालकाचे नाव:', cert.child_name],
            ['जन्म दिनांक:', cert.date_of_birth.strftime('%d/%m/%Y')],
            ['लिंग:', cert.get_child_gender_display()],
            ['जन्म स्थान:', cert.place_of_birth],
            ['वडिलांचे नाव:', cert.father_name],
            ['आईचे नाव:', cert.mother_name],
            ['कायमचा पत्ता:', cert.permanent_address],
        ]
    
    elif application.application_type == 'death_certificate':
        cert = application.death_certificate
        
        elements.append(Paragraph("मृत्यू प्रमाणपत्र", title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        cert_text = f"""
        ही प्रमाणित करण्यात येते की, खालील माहिती प्रमाणे मृत्यू नोंदविण्यात आला आहे.<br/>
        श्री./श्रीमती <b>{cert.deceased_name}</b> यांचा मृत्यू <b>{cert.date_of_death.strftime('%d/%m/%Y')}</b> 
        रोजी <b>{cert.place_of_death}</b> येथे झाला आहे.<br/><br/>
        मृताचे वय <b>{cert.deceased_age}</b> वर्षे आणि लिंग <b>{cert.get_deceased_gender_display()}</b> असून 
        मृत्यूचे कारण <b>{cert.cause_of_death}</b> असे नोंदविण्यात आले आहे.
        """
        elements.append(Paragraph(cert_text, normal_style))
        
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("प्रमाणपत्र तपशील:", label_style))
        elements.append(Spacer(1, 0.2*cm))
        
        details = [
            ['प्रमाणपत्र क्रमांक:', cert.certificate_number or 'N/A'],
            ['दिनांक:', cert.issued_date.strftime('%d/%m/%Y') if cert.issued_date else 'N/A'],
            ['मृताचे नाव:', cert.deceased_name],
            ['मृत्यू दिनांक:', cert.date_of_death.strftime('%d/%m/%Y')],
            ['वय:', f"{cert.deceased_age} वर्षे"],
            ['लिंग:', cert.get_deceased_gender_display()],
            ['मृत्यू स्थान:', cert.place_of_death],
            ['मृत्यूचे कारण:', cert.cause_of_death],
            ['कायमचा पत्ता:', cert.permanent_address],
        ]
    
    elif application.application_type == 'income_certificate':
        cert = application.income_certificate
        
        elements.append(Paragraph("उत्पन्न प्रमाणपत्र", title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        income_words = number_to_marathi_words(cert.annual_income)
        cert_text = f"""
        हे प्रमाणित करण्यात येते की श्री./श्रीमती <b>{cert.applicant_name}</b>, 
        रा. {cert.residential_address}, यांचे वार्षिक उत्पन्न रुपये <b>{cert.annual_income}</b> 
        (अक्षरी: {income_words} रुपये फक्त) आहे.<br/><br/>
        त्यांचे उत्पन्नाचे स्त्रोत <b>{cert.get_income_source_display()}</b> आहेत आणि ते <b>{cert.occupation}</b> व्यवसायात गुंतले आहेत.
        या प्रमाणपत्राची आवश्यकता <b>{cert.purpose_of_certificate}</b> साठी आहे.
        """
        elements.append(Paragraph(cert_text, normal_style))
        
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("प्रमाणपत्र तपशील:", label_style))
        elements.append(Spacer(1, 0.2*cm))
        
        details = [
            ['प्रमाणपत्र क्रमांक:', cert.certificate_number or 'N/A'],
            ['दिनांक:', cert.issued_date.strftime('%d/%m/%Y') if cert.issued_date else 'N/A'],
            ['वैध असे:', cert.valid_until.strftime('%d/%m/%Y') if cert.valid_until else 'N/A'],
            ['नाव:', cert.applicant_name],
            ['वडिलांचे / पतीचे नाव:', cert.father_husband_name],
            ['पत्ता:', cert.residential_address],
            ['वार्षिक उत्पन्न:', f"₹{cert.annual_income}"],
            ['व्यवसाय:', cert.occupation],
        ]
    
    else:
        return None
    
    # Create details table without borders (clean format)
    table = Table(details, colWidths=[4*cm, 8*cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), font_name + '-Bold' if font_name != 'Helvetica' else 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 2*cm))
    
    # Signature section
    elements.append(Spacer(1, 1*cm))
    
    # Create signature layout
    signature_data = [
        ['', 'ग्रामसेवक सही', 'सरपंच सही', 'अधिकृत शिक्का'],
        ['', '', '', ''],
    ]
    
    signature_table = Table(signature_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (0, -1), font_name),
        ('FONTNAME', (1, 0), (-1, 0), font_name + '-Bold' if font_name != 'Helvetica' else 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (-1, 1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (1, 1), (-1, 1), 20),
        ('LINEBELOW', (1, 1), (-1, 1), 1, colors.black),
    ]))
    
    elements.append(signature_table)
    elements.append(Spacer(1, 1*cm))
    
    # Footer
    elements.append(Paragraph("हे प्रमाणपत्र संगणकाद्वारे तयार केलेले असून त्यासाठी स्वाक्षरी आवश्यक नाही.", 
                          ParagraphStyle('Footer', parent=styles['Normal'], 
                                      fontSize=10, alignment=1, 
                                      fontName=font_name, wordWrap='CJK')))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ============================================

@login_required
def download_certificate(request, application_id):
    """
    Generate and download PDF certificate using HTML templates
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
    
    # Auto-generate certificate number if not exists
    if application.application_type == 'birth_certificate':
        cert = application.birth_certificate
        if not cert.certificate_number:
            cert.certificate_number = f"BC/{timezone.now().year}/{application.id:06d}"
            cert.save()
        
        context = {
            'certificate_number': cert.certificate_number,
            'issued_date': cert.issued_date or timezone.now(),
            'child_name': cert.child_name,
            'date_of_birth': cert.date_of_birth,
            'child_gender_display': cert.get_child_gender_display(),
            'place_of_birth': cert.place_of_birth,
            'father_name': cert.father_name,
            'mother_name': cert.mother_name,
            'permanent_address': cert.permanent_address,
            'district': 'पुणे',
            'taluka': 'हवेली',
            'gram_panchayat': 'मॉडेल ग्रामपंचायत',
        }
        template = 'portal_app/certificates/marathi_birth_certificate.html'
    
    elif application.application_type == 'death_certificate':
        cert = application.death_certificate
        if not cert.certificate_number:
            cert.certificate_number = f"DC/{timezone.now().year}/{application.id:06d}"
            cert.save()
        
        context = {
            'certificate_number': cert.certificate_number,
            'issued_date': cert.issued_date or timezone.now(),
            'deceased_name': cert.deceased_name,
            'date_of_death': cert.date_of_death,
            'deceased_age': cert.deceased_age,
            'deceased_gender_display': cert.get_deceased_gender_display(),
            'place_of_death': cert.place_of_death,
            'cause_of_death': cert.cause_of_death,
            'permanent_address': cert.permanent_address,
            'district': 'पुणे',
            'taluka': 'हवेली',
            'gram_panchayat': 'मॉडेल ग्रामपंचायत',
        }
        template = 'portal_app/certificates/marathi_death_certificate.html'
    
    elif application.application_type == 'income_certificate':
        cert = application.income_certificate
        if not cert.certificate_number:
            cert.certificate_number = f"IC/{timezone.now().year}/{application.id:06d}"
            cert.save()
        
        context = {
            'certificate_number': cert.certificate_number,
            'issued_date': cert.issued_date or timezone.now(),
            'valid_until': cert.valid_until,
            'applicant_name': cert.applicant_name,
            'father_husband_name': cert.father_husband_name,
            'occupation': cert.occupation,
            'annual_income': cert.annual_income,
            'annual_income_words': number_to_marathi_words(cert.annual_income) + ' रुपये फक्त',
            'income_source_display': cert.get_income_source_display(),
            'purpose_of_certificate': cert.purpose_of_certificate,
            'residential_address': cert.residential_address,
            'district': 'पुणे',
            'taluka': 'हवेली',
            'gram_panchayat': 'मॉडेल ग्रामपंचायत',
        }
        template = 'portal_app/certificates/marathi_income_certificate.html'
    
    else:
        messages.error(request, 'Certificate type not supported')
        return redirect('application_detail', application_id=application_id)
    
    if not application.certificate_pdf:
        _save_application_pdf(application)
        application.save(update_fields=['certificate_pdf'])

    if application.certificate_pdf:
        log_user_activity(
            user=request.user,
            action='document_downloaded',
            description=f'Downloaded certificate/document for {application.application_number}.',
            application=application,
            reference=application.application_number
        )

        return FileResponse(
            application.certificate_pdf.open('rb'),
            as_attachment=True,
            filename=f"{application.application_number}.pdf"
        )

    messages.error(request, 'Unable to generate certificate PDF at the moment.')
    if request.user == application.applicant:
        return redirect('application_detail', application_id=application_id)
    return redirect('admin_applications')
    
    # Fallback to old table-based method
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
    
    # Header
    elements.append(Paragraph("महाराष्ट्र शासन", title_style))
    elements.append(Paragraph("डिजिटल ग्रामपंचायत पोर्टल", styles['Heading2']))
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

@require_http_methods(["GET", "POST"])
def verify_otp_view(request):
    """
    OTP Verification View
    
    Flow:
    1. User receives OTP via email after registration
    2. User enters 6-digit OTP
    3. OTP validated (expiration, attempts, correctness)
    4. Account activated on successful verification
    
    Security:
    - OTP expires in 1 minute
    - Maximum 3 verification attempts per OTP
    - One-time use only
    - Rate limiting on resend (1 per minute)
    """
    # Always resolve pending user from session user ID first.
    user_id = request.session.get('pending_user_id') or request.session.get('pending_verification_user_id')
    
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if not user_id:
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'No pending verification found.', 'redirect_url': reverse('register')}, status=400)
        messages.error(request, 'No pending verification found. Please register again.')
        return redirect('register')

    # Keep both keys in sync for compatibility across old/new OTP flows.
    request.session['pending_user_id'] = user_id
    request.session['pending_verification_user_id'] = user_id
    request.session.modified = True
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'Invalid verification session.', 'redirect_url': reverse('register')}, status=400)
        messages.error(request, 'Invalid verification session. Please register again.')
        return redirect('register')
    
    # Check if already verified
    if user.email_verified:
        if is_ajax:
            return JsonResponse({'success': True, 'message': 'Your email is already verified.', 'redirect_url': reverse('login')})
        messages.info(request, 'Your email is already verified. Please login.')
        request.session.pop('pending_verification_user_id', None)
        request.session.pop('pending_user_id', None)
        request.session.modified = True
        return redirect('login')
    
    # Get latest OTP for user
    from .models import EmailOTP
    latest_otp = EmailOTP.objects.filter(user=user).order_by('-id').first()
    
    if request.method == 'POST':
        from .security_utils import check_rate_limit, rate_limit_exceeded_response
        client_ip = get_client_ip(request)
        rate_limit_id = f"otp_verify:{user.id}:{client_ip}"
        if not check_rate_limit(rate_limit_id, limit=10, period=600):
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Too many verification attempts. Please try later.'}, status=429)
            return rate_limit_exceeded_response()

        form = OTPVerificationForm(request.POST)
        
        if form.is_valid():
            otp_code = _normalize_otp_code(form.cleaned_data.get('otp_code') or request.POST.get('otp') or request.POST.get('otp_code'))
            otp_obj = EmailOTP.objects.filter(user=user).order_by('-id').first()

            print("Entered OTP:", request.POST.get("otp"))
            print("Entered OTP (otp_code field):", request.POST.get("otp_code"))
            print("Session User ID:", request.session.get("pending_user_id"))
            print("Stored OTP from DB:", (getattr(otp_obj, "otp", None) or getattr(otp_obj, "otp_code", None)) if otp_obj else None)

            success = False
            message = 'Invalid OTP code.'

            if not otp_obj:
                message = 'No OTP found. Please request a new OTP.'
            elif len(str(otp_code)) != 6:
                message = 'Please enter a valid 6-digit OTP.'
            elif otp_obj.is_used or otp_obj.is_verified:
                message = 'This OTP has already been used. Please request a new OTP.'
            elif timezone.now() > otp_obj.expires_at:
                otp_obj.is_used = True
                otp_obj.save(update_fields=['is_used'])
                message = 'OTP expired after 5 minutes. Please click Resend OTP.'
            elif otp_obj.verification_attempts >= 3:
                otp_obj.is_used = True
                otp_obj.save(update_fields=['is_used'])
                message = 'Maximum attempts exceeded. Please request a new OTP.'
            else:
                entered_otp = str(otp_code).strip()
                stored_otp = str(otp_obj.otp_code).strip()

                # String-safe compare for legacy plaintext rows; hashed rows use secure verifier.
                otp_matches = (entered_otp == stored_otp)
                if hasattr(otp_obj, 'verify_otp_code'):
                    otp_matches = otp_obj.verify_otp_code(entered_otp)

                otp_obj.verification_attempts += 1
                update_fields = ['verification_attempts']

                if otp_matches:
                    otp_obj.is_verified = True
                    otp_obj.is_used = True
                    otp_obj.verified_at = timezone.now()
                    update_fields.extend(['is_verified', 'is_used', 'verified_at'])
                    otp_obj.save(update_fields=update_fields)

                    user.email_verified = True
                    user.email_verified_at = timezone.now()
                    if user.role == 'citizen':
                        user.is_active = True
                        message = 'Email verified successfully! You can now login.'
                    else:
                        user.is_active = False
                        message = 'Email verified successfully! Your account is pending administrator approval.'
                    user.save(update_fields=['email_verified', 'email_verified_at', 'is_active'])
                    success = True
                else:
                    if otp_obj.verification_attempts >= 3:
                        otp_obj.is_used = True
                        update_fields.append('is_used')
                    otp_obj.save(update_fields=update_fields)
                    attempts_left = max(0, 3 - otp_obj.verification_attempts)
                    message = f'Invalid OTP code. {attempts_left} attempt(s) remaining.'
            
            if success:
                if is_ajax:
                    request.session.pop('pending_verification_user_id', None)
                    request.session.pop('pending_user_id', None)
                    request.session.modified = True
                    return JsonResponse({'success': True, 'message': message, 'redirect_url': reverse('login')})
                messages.success(request, message)
                request.session.pop('pending_verification_user_id', None)
                request.session.pop('pending_user_id', None)
                request.session.modified = True
                return redirect('login')
            else:
                if is_ajax:
                    return JsonResponse({'success': False, 'message': message}, status=400)
                messages.error(request, message)
        else:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Please enter a valid 6-digit OTP.'}, status=400)
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


@require_POST
def resend_otp_view(request):
    """
    Resend OTP View
    
    Security:
    - Rate limiting: 1 OTP per minute
    - Invalidates previous OTPs
    - CSRF protection via POST method
    """
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    
    # Get user ID from session
    user_id = request.session.get('pending_verification_user_id')
    
    if not user_id:
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'No pending verification found.', 'redirect_url': reverse('register')}, status=400)
        messages.error(request, 'No pending verification found.')
        return redirect('register')
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'Invalid verification session.', 'redirect_url': reverse('register')}, status=400)
        messages.error(request, 'Invalid verification session.')
        return redirect('register')
    
    from .security_utils import check_rate_limit, rate_limit_exceeded_response
    client_ip = get_client_ip(request)
    rate_limit_id = f"otp_resend:{user.id}:{client_ip}"
    if not check_rate_limit(rate_limit_id, limit=3, period=600):
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'Too many resend requests. Please try later.'}, status=429)
        return rate_limit_exceeded_response()

    # Resend OTP
    from .security_utils import resend_otp
    success, message = resend_otp(user)
    
    if is_ajax:
        status = 200 if success else 400
        return JsonResponse({'success': success, 'message': message}, status=status)

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return redirect('verify_otp')

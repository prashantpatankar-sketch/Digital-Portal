from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Count
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from .models import Application, CustomUser, UserActivity
from .email_utils import get_branded_from_email


CERTIFICATE_TYPES = [
    'birth_certificate',
    'death_certificate',
    'income_certificate',
]

BILL_TYPES = [
    'bill_request',
    'water_tax',
    'house_tax',
]


def _month_start(dt):
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _next_month(dt):
    if dt.month == 12:
        return dt.replace(year=dt.year + 1, month=1, day=1)
    return dt.replace(month=dt.month + 1, day=1)


def _safe_percent_change(current, previous):
    if previous <= 0:
        if current <= 0:
            return 0.0
        return 100.0
    return round(((current - previous) / previous) * 100.0, 1)


def _monthly_series(month_count=6):
    now = timezone.now()
    current_start = _month_start(now)
    starts = []
    cursor = current_start
    for _ in range(month_count - 1):
        if cursor.month == 1:
            cursor = cursor.replace(year=cursor.year - 1, month=12)
        else:
            cursor = cursor.replace(month=cursor.month - 1)
        starts.append(cursor)
    starts.reverse()
    starts.append(current_start)

    labels = [start.strftime('%b %Y') for start in starts]
    ranges = [(start, _next_month(start)) for start in starts]
    return labels, ranges


def collect_admin_analytics():
    now = timezone.now()
    today = now.date()

    active_since = now - timedelta(days=30)

    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True, last_login__gte=active_since).count()
    inactive_users = max(total_users - active_users, 0)

    total_applications = Application.objects.count()
    certificates_issued = Application.objects.filter(
        application_type__in=CERTIFICATE_TYPES,
        status='approved'
    ).count()
    pending_requests = Application.objects.filter(status__in=['pending', 'under_review']).count()

    current_month_start = _month_start(now)
    previous_month_start = _month_start(
        current_month_start - timedelta(days=1)
    )

    users_current = CustomUser.objects.filter(created_at__gte=current_month_start).count()
    users_previous = CustomUser.objects.filter(
        created_at__gte=previous_month_start,
        created_at__lt=current_month_start
    ).count()

    apps_current = Application.objects.filter(applied_date__gte=current_month_start).count()
    apps_previous = Application.objects.filter(
        applied_date__gte=previous_month_start,
        applied_date__lt=current_month_start
    ).count()

    cert_current = Application.objects.filter(
        application_type__in=CERTIFICATE_TYPES,
        status='approved',
        reviewed_date__gte=current_month_start
    ).count()
    cert_previous = Application.objects.filter(
        application_type__in=CERTIFICATE_TYPES,
        status='approved',
        reviewed_date__gte=previous_month_start,
        reviewed_date__lt=current_month_start
    ).count()

    labels, ranges = _monthly_series(month_count=6)

    user_growth_values = []
    monthly_app_values = []
    for start, end in ranges:
        user_growth_values.append(
            CustomUser.objects.filter(created_at__gte=start, created_at__lt=end).count()
        )
        monthly_app_values.append(
            Application.objects.filter(applied_date__gte=start, applied_date__lt=end).count()
        )

    cert_labels = ['Birth', 'Death', 'Income']
    cert_keys = ['birth_certificate', 'death_certificate', 'income_certificate']
    cert_values = [
        Application.objects.filter(application_type=key, status='approved').count()
        for key in cert_keys
    ]

    week_labels = []
    week_values = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        day_start = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time()))
        day_end = day_start + timedelta(days=1)
        day_count = UserActivity.objects.filter(created_at__gte=day_start, created_at__lt=day_end).count()
        if day_count == 0:
            day_count = Application.objects.filter(applied_date__gte=day_start, applied_date__lt=day_end).count()
        week_labels.append(day.strftime('%d %b'))
        week_values.append(day_count)

    cert_request_counts = Application.objects.filter(
        application_type__in=CERTIFICATE_TYPES
    ).values('application_type').annotate(total=Count('id')).order_by('-total')

    if cert_request_counts:
        top_cert = cert_request_counts[0]['application_type'].replace('_', ' ').title()
    else:
        top_cert = 'No certificate requests yet'

    hour_buckets = UserActivity.objects.extra(
        select={'hour': 'HOUR(created_at)'}
    ).values('hour').annotate(total=Count('id')).order_by('-total')

    if hour_buckets:
        peak_hour = int(hour_buckets[0]['hour'])
        peak_label = f"{peak_hour:02d}:00 - {peak_hour:02d}:59"
    else:
        peak_label = 'Insufficient activity data'

    insights = [
        f"User registrations changed by {_safe_percent_change(users_current, users_previous)}% this month.",
        f"Most requested certificate: {top_cert}.",
        f"Peak activity time: {peak_label}.",
    ]

    return {
        'generated_at': now,
        'overview': {
            'total_users': total_users,
            'active_users': active_users,
            'total_applications': total_applications,
            'certificates_issued': certificates_issued,
            'pending_requests': pending_requests,
        },
        'trends': {
            'users': _safe_percent_change(users_current, users_previous),
            'applications': _safe_percent_change(apps_current, apps_previous),
            'certificates': _safe_percent_change(cert_current, cert_previous),
            'active_users': _safe_percent_change(active_users, inactive_users),
            'pending': _safe_percent_change(pending_requests, apps_previous),
        },
        'charts': {
            'user_growth': {
                'labels': labels,
                'values': user_growth_values,
            },
            'monthly_applications': {
                'labels': labels,
                'values': monthly_app_values,
            },
            'certificate_distribution': {
                'labels': cert_labels,
                'values': cert_values,
            },
            'active_vs_inactive': {
                'labels': ['Active', 'Inactive'],
                'values': [active_users, inactive_users],
            },
            'monthly_activity': {
                'labels': week_labels,
                'values': week_values,
            },
        },
        'insights': insights,
    }


def send_admin_report_email(period='daily', triggered_by=None):
    analytics = collect_admin_analytics()

    configured = getattr(settings, 'ADMIN_REPORT_RECIPIENTS', [])
    recipients = [email for email in configured if email]
    if not recipients:
        recipients = list(
            CustomUser.objects.filter(role='admin').exclude(email='').values_list('email', flat=True)
        )

    recipients = sorted(set(recipients))
    if not recipients:
        return False, 'No admin email recipients configured.'

    date_label = timezone.localtime(analytics['generated_at']).strftime('%d %b %Y %I:%M %p')
    subject = f"Digital Grampanchayat {period.title()} Analytics Report - {date_label}"

    html_body = render_to_string('portal_app/emails/admin_report.html', {
        'period': period,
        'analytics': analytics,
        'triggered_by': triggered_by,
        'admin_dashboard_url': reverse('admin_dashboard'),
    })

    plain_body = (
        f"{period.title()} Analytics Report\n"
        f"Generated at: {date_label}\n\n"
        f"Total Users: {analytics['overview']['total_users']}\n"
        f"Active Users: {analytics['overview']['active_users']}\n"
        f"Total Applications: {analytics['overview']['total_applications']}\n"
        f"Certificates Issued: {analytics['overview']['certificates_issued']}\n"
        f"Pending Requests: {analytics['overview']['pending_requests']}\n"
    )

    from_email = get_branded_from_email()
    mail = EmailMultiAlternatives(
        subject=subject,
        body=plain_body,
        from_email=from_email,
        to=recipients,
    )
    mail.content_subtype = 'plain'
    mail.attach_alternative(html_body, 'text/html')

    try:
        mail.send(fail_silently=False)
    except Exception as exc:  # pragma: no cover - operational safety
        return False, str(exc)

    return True, f'Report sent to {len(recipients)} admin recipient(s).'

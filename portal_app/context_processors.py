"""Shared UI context values for dashboard badges and counters."""

from .models import Application, Complaint, Notification


def ui_badges(request):
    """Expose sidebar badge counts for authenticated users."""
    defaults = {
        'ui_badges': {
            'notifications': 0,
            'pending_applications': 0,
            'complaints': 0,
        }
    }

    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return defaults

    notification_count = Notification.objects.filter(recipient=user, is_read=False).count()

    if user.role in ['admin', 'staff']:
        pending_count = Application.objects.filter(status='pending').count()
        complaints_count = Complaint.objects.filter(status__in=['open', 'in_progress']).count()
    else:
        pending_count = Application.objects.filter(applicant=user, status='pending').count()
        complaints_count = Complaint.objects.filter(
            complainant=user,
            status__in=['open', 'in_progress']
        ).count()

    return {
        'ui_badges': {
            'notifications': notification_count,
            'pending_applications': pending_count,
            'complaints': complaints_count,
        }
    }

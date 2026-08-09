"""
Django management command to safely delete all non-admin users.
Usage: python manage.py delete_non_admin_users [--force]
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.sessions.models import Session
from portal_app.models import (
    Application,
    Complaint,
    CustomUser,
    EmailOTP,
    Notification,
    PendingRegistration,
    UserActivity,
)


def _force_logout_user_ids(user_ids):
    """Delete active sessions for targeted users before account deletion."""
    if not user_ids:
        return 0

    deleted_sessions = 0
    for session in Session.objects.all().iterator():
        try:
            data = session.get_decoded()
        except Exception:
            continue

        auth_user_id = data.get('_auth_user_id')
        if auth_user_id and str(auth_user_id) in user_ids:
            session.delete()
            deleted_sessions += 1

    return deleted_sessions


def _count_related_data(user_ids):
    """Count related data that should disappear with user deletion."""
    if not user_ids:
        return {
            'applications': 0,
            'complaints': 0,
            'email_otps': 0,
            'notifications': 0,
            'activity_logs': 0,
        }

    return {
        'applications': Application.objects.filter(applicant_id__in=user_ids).count(),
        'complaints': Complaint.objects.filter(complainant_id__in=user_ids).count(),
        'email_otps': EmailOTP.objects.filter(user_id__in=user_ids).count(),
        'notifications': Notification.objects.filter(recipient_id__in=user_ids).count(),
        'activity_logs': UserActivity.objects.filter(user_id__in=user_ids).count(),
    }


class Command(BaseCommand):
    help = 'Safely delete all non-admin/non-superuser users and their related data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation and proceed with deletion',
        )
        parser.add_argument(
            '--keep-sessions',
            action='store_true',
            help='Keep sessions after deletion (not recommended for reset flows)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('SAFE USER DELETION'))
        self.stdout.write(self.style.WARNING('=' * 70))

        # Count users
        users_to_delete = CustomUser.objects.filter(
            role__in=['citizen', 'staff']
        ).exclude(is_superuser=True)

        citizen_users = users_to_delete.filter(role='citizen')
        staff_users = users_to_delete.filter(role='staff')
        admin_users = CustomUser.objects.filter(role='admin')
        superusers = CustomUser.objects.filter(is_superuser=True)
        target_user_ids = list(users_to_delete.values_list('id', flat=True))
        related = _count_related_data(target_user_ids)
        pending_registrations = PendingRegistration.objects.count()

        citizens_count = citizen_users.count()
        staff_count = staff_users.count()

        self.stdout.write(f"\nUsers to DELETE:")
        self.stdout.write(f"  • Citizens: {citizens_count}")
        self.stdout.write(f"  • Staff: {staff_count}")
        self.stdout.write(f"  • TOTAL TO DELETE: {citizens_count + staff_count}")

        self.stdout.write(f"\nUsers to PROTECT:")
        self.stdout.write(f"  • Admins: {admin_users.count()}")
        self.stdout.write(f"  • Superusers: {superusers.count()}")

        self.stdout.write(f"\nRelated data to DELETE:")
        self.stdout.write(f"  • Applications: {related['applications']}")
        self.stdout.write(f"  • Complaints: {related['complaints']}")
        self.stdout.write(f"  • OTP records (EmailOTP): {related['email_otps']}")
        self.stdout.write(f"  • Notifications: {related['notifications']}")
        self.stdout.write(f"  • Activity logs: {related['activity_logs']}")
        self.stdout.write(f"  • Pending registrations: {pending_registrations}")

        total_to_delete = citizens_count + staff_count

        if total_to_delete == 0 and pending_registrations == 0:
            self.stdout.write(self.style.SUCCESS('✓ No users or pending registrations to delete.'))
            return

        if not options['force']:
            self.stdout.write(self.style.WARNING(
                f'\n⚠️  This will delete {total_to_delete} users and reset registration state:'
            ))
            self.stdout.write('  • Applications (Birth, Death, Income Certificates)')
            self.stdout.write('  • Complaints')
            self.stdout.write('  • Bills (Electricity, Water, Property Tax)')
            self.stdout.write('  • OTP records linked to deleted users')
            self.stdout.write('  • Pending registrations (for clean re-registration)')
            self.stdout.write('  • Activity logs and notifications')
            if not options['keep_sessions']:
                self.stdout.write('  • All sessions (forces logout for logged in users)')
            self.stdout.write('\nType "yes" to confirm deletion:')
            
            confirmation = input().strip().lower()
            if confirmation != 'yes':
                self.stdout.write(self.style.ERROR('❌ Deletion cancelled.'))
                return

        # Perform deletion in one atomic unit
        deleted_count = 0
        pending_deleted = 0
        force_logged_out = 0
        sessions_deleted = 0

        with transaction.atomic():
            target_user_ids_str = {str(value) for value in target_user_ids}
            force_logged_out = _force_logout_user_ids(target_user_ids_str)

            self.stdout.write(self.style.WARNING(f'\n🗑️  Deleting {total_to_delete} users...'))
            deleted_count, _ = users_to_delete.delete()

            # Remove pending registration rows so fresh signup is not blocked by stale unique values.
            pending_deleted, _ = PendingRegistration.objects.all().delete()

            # Clear sessions to invalidate all active logins unless explicitly skipped.
            if not options['keep_sessions']:
                sessions_deleted, _ = Session.objects.all().delete()

        if force_logged_out:
            self.stdout.write(self.style.WARNING(f'Forced logout for {force_logged_out} targeted active session(s).'))
        if not options['keep_sessions']:
            self.stdout.write(self.style.WARNING(f'Cleared {sessions_deleted} session(s) from session store.'))
        self.stdout.write(self.style.WARNING(f'Removed {pending_deleted} pending registration record(s).'))

        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully deleted all non-admin users'))
        self.stdout.write(self.style.SUCCESS(f'✓ Total records deleted: {deleted_count}'))

        # Final verification
        self.stdout.write(self.style.WARNING('\n' + '=' * 70))
        self.stdout.write(self.style.WARNING('FINAL STATUS:'))
        self.stdout.write(self.style.WARNING('=' * 70))
        
        remaining_citizens = CustomUser.objects.filter(role='citizen').count()
        remaining_staff = CustomUser.objects.filter(role='staff').count()
        remaining_admins = CustomUser.objects.filter(role='admin').count()
        remaining_superusers = CustomUser.objects.filter(is_superuser=True).count()
        total_remaining = CustomUser.objects.count()
        remaining_pending = PendingRegistration.objects.count()
        remaining_email_otps_for_deleted_users = EmailOTP.objects.filter(
            user__role__in=['citizen', 'staff']
        ).count()

        username_conflicts = PendingRegistration.objects.filter(
            username__in=CustomUser.objects.values_list('username', flat=True)
        ).count()
        email_conflicts = PendingRegistration.objects.filter(
            email__in=CustomUser.objects.values_list('email', flat=True)
        ).count()

        self.stdout.write(f"Citizens remaining: {remaining_citizens}")
        self.stdout.write(f"Staff remaining: {remaining_staff}")
        self.stdout.write(f"Admins remaining: {remaining_admins}")
        self.stdout.write(f"Superusers remaining: {remaining_superusers}")
        self.stdout.write(f"Pending registrations remaining: {remaining_pending}")
        self.stdout.write(f"OTP records for citizen/staff users remaining: {remaining_email_otps_for_deleted_users}")
        self.stdout.write(f"Pending registration username conflicts: {username_conflicts}")
        self.stdout.write(f"Pending registration email conflicts: {email_conflicts}")
        self.stdout.write(f"TOTAL USERS: {total_remaining}")
        self.stdout.write(self.style.SUCCESS('\n✓ Deletion complete!'))

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from portal_app.models import ElectricityBill, WaterBill, PropertyTaxRecord, Notification
from portal_app.email_utils import send_official_email


class Command(BaseCommand):
    help = 'Send bill reminder emails and in-app notifications for upcoming due bills.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=5,
            help='Send reminders for unpaid bills due within this many days (default: 5).'
        )

    def handle(self, *args, **options):
        days = max(1, options['days'])
        today = timezone.localdate()
        due_limit = today + timedelta(days=days)

        total_sent = 0
        total_failed = 0

        sources = [
            (
                ElectricityBill.objects.filter(
                    payment_status='unpaid',
                    due_date__gte=today,
                    due_date__lte=due_limit,
                ).select_related('user'),
                'Electricity Bill Reminder',
                'electricity-bill',
                lambda bill: bill.consumer_number,
                lambda bill: f'electricity:{bill.id}'
            ),
            (
                WaterBill.objects.filter(
                    payment_status='unpaid',
                    due_date__gte=today,
                    due_date__lte=due_limit,
                ).select_related('user'),
                'Water Bill Reminder',
                'water-bill',
                lambda bill: bill.connection_number,
                lambda bill: f'water:{bill.id}'
            ),
            (
                PropertyTaxRecord.objects.filter(
                    payment_status='unpaid',
                    due_date__gte=today,
                    due_date__lte=due_limit,
                ).select_related('user'),
                'Property Tax Reminder',
                'property-tax',
                lambda bill: bill.property_number,
                lambda bill: f'property:{bill.id}'
            ),
        ]

        for queryset, reminder_title, route_slug, ref_fn, key_fn in sources:
            for bill in queryset:
                user = bill.user
                if not user or not user.email:
                    total_failed += 1
                    continue

                reference = ref_fn(bill)
                unique_key = key_fn(bill)

                duplicate_today = Notification.objects.filter(
                    recipient=user,
                    category='bill',
                    title=reminder_title,
                    message__icontains=unique_key,
                    created_at__date=today,
                ).exists()

                if duplicate_today:
                    continue

                days_left = (bill.due_date - today).days
                message = (
                    f'Your {reminder_title.replace(" Reminder", "")} ({reference}) '
                    f'is due on {bill.due_date:%d %b %Y}. '
                    f'Please complete payment in {days_left} day(s). [{unique_key}]'
                )

                Notification.objects.create(
                    recipient=user,
                    title=reminder_title,
                    message=message,
                    category='bill',
                    target_url=f'/services/{route_slug}/'
                )

                try:
                    send_official_email(
                        to_email=user.email,
                        subject=reminder_title,
                        greeting_name='User',
                        intro_text='This is a bill payment reminder from Digital Grampanchayat Portal.',
                        body_lines=[
                            message,
                            'Please login to the portal and complete payment before the due date.'
                        ],
                        cta_text='Open Bill Services',
                        cta_url=f'/services/{route_slug}/',
                        reference_text=f'Reference: {unique_key}',
                    )
                    total_sent += 1
                except Exception as exc:
                    total_failed += 1
                    self.stdout.write(self.style.WARNING(f'Email failed for {user.email}: {exc}'))

        self.stdout.write(
            self.style.SUCCESS(
                f'Bill reminders completed. Sent: {total_sent}, Failed: {total_failed}, Window: {days} day(s).'
            )
        )

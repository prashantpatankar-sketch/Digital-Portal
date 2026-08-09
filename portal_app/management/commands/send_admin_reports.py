from django.core.management.base import BaseCommand

from portal_app.admin_analytics import send_admin_report_email


class Command(BaseCommand):
    help = 'Send scheduled admin analytics report emails.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--period',
            default='daily',
            choices=['daily', 'weekly'],
            help='Report period label for subject and body.',
        )

    def handle(self, *args, **options):
        period = options['period']
        ok, message = send_admin_report_email(period=period, triggered_by='scheduler')

        if ok:
            self.stdout.write(self.style.SUCCESS(message))
        else:
            self.stderr.write(self.style.ERROR(message))

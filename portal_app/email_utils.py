from email.utils import formataddr

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


# Inline SVG crest-like icon encoded as a data URI for broad email compatibility.
PORTAL_LOGO_DATA_URI = (
    'data:image/svg+xml;base64,'
    'PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI5NiIgaGVpZ2h0PSI5NiIgdmlld0JveD0iMCAwIDk2IDk2Ij4K'
    'ICA8ZGVmcz4KICAgIDxsaW5lYXJHcmFkaWVudCBpZD0iZyIgeDE9IjAlIiB5MT0iMCUiIHgyPSIxMDAlIiB5Mj0iMTAwJSI+CiAgICAgIDxzdG9w'
    'IG9mZnNldD0iMCUiIHN0b3AtY29sb3I9IiMxZTNhOGEiLz4KICAgICAgPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdG9wLWNvbG9yPSIjMTcyNTU0Ii8+'
    'CiAgICA8L2xpbmVhckdyYWRpZW50PgogIDwvZGVmcz4KICA8cmVjdCB4PSI4IiB5PSI4IiB3aWR0aD0iODAiIGhlaWdodD0iODAiIHJ4PSIxNiIg'
    'ZmlsbD0idXJsKCNnKSIvPgogIDxwYXRoIGQ9Ik00OCAyNEMzOSAyNCAzMiAzMSAzMiA0MHY4YzAgMTIgNyAyMiAxNiAyNiA5LTQgMTYtMTQgMTYt'
    'MjZ2LThjMC05LTctMTYtMTYtMTZ6IiBmaWxsPSIjZmZmIi8+CiAgPHJlY3QgeD0iNDAiIHk9IjM4IiB3aWR0aD0iMTYiIGhlaWdodD0iMyIgcng9'
    'IjEiIGZpbGw9IiMxZTNhOGEiLz4KICA8cmVjdCB4PSI0MCIgeT0iNDQiIHdpZHRoPSIxNiIgaGVpZ2h0PSIzIiByeD0iMSIgZmlsbD0iIzFlM2E4'
    'YSIvPgogIDxyZWN0IHg9IjQwIiB5PSI1MCIgd2lkdGg9IjE2IiBoZWlnaHQ9IjMiIHJ4PSIxIiBmaWxsPSIjMWUzYThhIi8+CiAgPGNpcmNsZSBj'
    'eD0iNDgiIGN5PSI2OCIgcj0iNCIgZmlsbD0iI2ZmZiIvPgo8L3N2Zz4K'
)


def get_branded_from_email():
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
    from_name = getattr(settings, 'EMAIL_FROM_NAME', 'Digital Grampanchayat Portal')
    return formataddr((from_name, from_email))


def send_official_email(
    *,
    to_email,
    subject,
    greeting_name='User',
    intro_text='',
    body_lines=None,
    otp_code=None,
    otp_expiry_minutes=5,
    cta_text='',
    cta_url='',
    reference_text='',
    help_text='For assistance, please contact the official support desk.',
    footer_note='This is an official communication from Digital Grampanchayat Portal.',
    attachments=None,
):
    """Send branded HTML + plain-text email while preserving SMTP backend behavior."""
    body_lines = body_lines or []
    attachments = attachments or []

    context = {
        'portal_title': 'Digital Grampanchayat Portal',
        'greeting_name': greeting_name or 'User',
        'subject_title': subject,
        'intro_text': intro_text,
        'body_lines': body_lines,
        'otp_code': otp_code,
        'otp_expiry_minutes': otp_expiry_minutes,
        'cta_text': cta_text,
        'cta_url': cta_url,
        'reference_text': reference_text,
        'help_text': help_text,
        'footer_note': footer_note,
        'logo_data_uri': PORTAL_LOGO_DATA_URI,
    }

    html_body = render_to_string('portal_app/emails/official_notification.html', context)
    plain_body = strip_tags(html_body)

    mail = EmailMultiAlternatives(
        subject=subject,
        body=plain_body,
        from_email=get_branded_from_email(),
        to=[to_email],
    )
    mail.attach_alternative(html_body, 'text/html')

    for filename, content, mimetype in attachments:
        mail.attach(filename, content, mimetype)

    mail.send(fail_silently=False)
    return True

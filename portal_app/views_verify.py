from django.shortcuts import render
from django.http import HttpResponse
from portal_app.models import Application
from django.utils.html import format_html

def verify_certificate(request):
    cert_id = request.GET.get('certificate_id')
    cert = None
    status = 'invalid'
    cert_type = name = issue_date = None
    if cert_id:
        cert = Application.objects.filter(application_number=cert_id, status='approved').first()
        if cert:
            status = 'valid'
            cert_type = cert.get_application_type_display()
            name = cert.applicant.get_full_name()
            issue_date = cert.applied_date.strftime('%d-%m-%Y')
    return render(request, 'portal_app/verify_certificate.html', {
        'status': status,
        'cert_type': cert_type,
        'name': name,
        'issue_date': issue_date,
        'cert_id': cert_id,
    })

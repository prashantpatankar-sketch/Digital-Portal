from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os
from django.conf import settings

def generate_certificate_pdf(cert, applicant, qr_path, signatures, output_filename):
    # Register Marathi font
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'NotoSansMarathi-Regular.ttf')
    pdfmetrics.registerFont(TTFont('NotoMarathi', font_path))
    c = canvas.Canvas(output_filename, pagesize=A4)
    width, height = A4

    # Header
    c.setFont('NotoMarathi', 18)
    c.drawCentredString(width/2, height-40, cert.panchayat_name)
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(width/2, height-70, cert.get_bilingual_title())

    # Applicant details
    c.setFont('Helvetica', 12)
    c.drawString(40, height-110, f"Name: {applicant.name}")
    c.drawString(40, height-130, f"DOB: {applicant.dob}")
    c.drawString(40, height-150, f"Address: {applicant.address}")

    # Official declaration
    c.setFont('NotoMarathi', 12)
    c.drawString(40, height-180, cert.get_official_marathi_text())
    c.setFont('Helvetica', 12)
    c.drawString(40, height-200, cert.get_official_english_text())

    # QR code
    c.drawImage(qr_path, width-120, height-220, 80, 80)

    # Signatures
    y_sig = height-260
    for sig in signatures:
        c.drawImage(sig.image.path, 40, y_sig, 60, 30)
        c.setFont('Helvetica', 10)
        c.drawString(110, y_sig+10, sig.role)
        y_sig -= 40

    # Seal placeholder
    c.setFont('Helvetica-Bold', 12)
    c.setFillColor(colors.grey)
    c.drawString(width-120, 60, "[Official Seal]")
    c.setFillColor(colors.black)

    # Footer
    c.setFont('Helvetica', 9)
    c.drawCentredString(width/2, 40, "This certificate is digitally generated and verifiable.")

    c.showPage()
    c.save()
    return output_filename

# Usage in view:
# pdf_path = generate_certificate_pdf(cert, applicant, cert.qr_code.path, [gram_sevak_sig, sarpanch_sig], output_filename)
# response = FileResponse(open(pdf_path, 'rb'), content_type='application/pdf')
# response['Content-Disposition'] = f'attachment; filename="certificate_{cert.id}.pdf"'
# return response

import qrcode
import os
from django.conf import settings
from django.core.files import File
from datetime import datetime

def generate_certificate_qr(certificate_id, issue_date, panchayat_name, verification_url):
    qr_data = f"Certificate ID: {certificate_id}\nIssue Date: {issue_date}\nPanchayat: {panchayat_name}\nVerify: {verification_url}"
    qr = qrcode.make(qr_data)
    qr_dir = os.path.join(settings.MEDIA_ROOT, 'certificates', 'qr')
    os.makedirs(qr_dir, exist_ok=True)
    filename = f"qr_{certificate_id}.png"
    file_path = os.path.join(qr_dir, filename)
    qr.save(file_path)
    return os.path.join('certificates', 'qr', filename)

# Example model field:
# qr_code = models.ImageField(upload_to='certificates/qr/', blank=True, null=True)

# Example usage in views.py:
# qr_path = generate_certificate_qr(cert.id, cert.issue_date, cert.panchayat_name, cert.get_verification_url())
# cert.qr_code = qr_path
# cert.save()

def number_to_marathi_words(number):
    """
    Convert number to Marathi words
    Basic implementation for income amounts
    """
    if not number:
        return ""
    
    units = ["", "एक", "दोन", "तीन", "चार", "पाच", "सहा", "सात", "आठ", "नऊ", "दहा"]
    tens = ["", "दहा", "वीस", "तीस", "चाळीस", "पन्नास", "साठ", "सत्तर", "अस्सी", "नव्वद"]
    
    try:
        num = int(number)
        if num == 0:
            return "शून्य"
        elif num <= 10:
            return units[num]
        elif num < 100:
            return tens[num // 10] + (" " + units[num % 10] if num % 10 != 0 else "")
        elif num < 1000:
            return units[num // 100] + "शे" + (" " + number_to_marathi_words(num % 100) if num % 100 != 0 else "")
        elif num < 100000:
            return number_to_marathi_words(num // 1000) + " हजार" + (" " + number_to_marathi_words(num % 1000) if num % 1000 != 0 else "")
        elif num < 10000000:
            return number_to_marathi_words(num // 100000) + " लाख" + (" " + number_to_marathi_words(num % 100000) if num % 100000 != 0 else "")
        else:
            return str(number)  # Fallback for very large numbers
    except:
        return str(number)

def get_marathi_date(date_obj):
    """
    Convert date object to Marathi format
    """
    if not date_obj:
        return ""
    
    marathi_months = [
        "जानेवारी", "फेब्रुवारी", "मार्च", "एप्रिल", "मे", "जून",
        "जुलै", "ऑगस्ट", "सप्टेंबर", "ऑक्टोबर", "नोव्हेंबर", "डिसेंबर"
    ]
    
    try:
        return f"{date_obj.day} {marathi_months[date_obj.month - 1]} {date_obj.year}"
    except:
        return str(date_obj)

def format_marathi_address(address):
    """
    Format address in proper Marathi style
    """
    if not address:
        return ""
    
    # Basic formatting - can be enhanced
    return address.strip().title()

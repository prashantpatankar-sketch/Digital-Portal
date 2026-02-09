"""
Security Utilities for Gram Panchayat Portal

Provides helper functions for:
- Input sanitization
- File validation
- Rate limiting helpers
- Security logging
"""

import os
import re
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.core.files.uploadedfile import UploadedFile


# ============================================
# INPUT SANITIZATION
# ============================================

def sanitize_input(text, allow_html=False):
    """
    Sanitize user input to prevent XSS attacks
    
    Args:
        text (str): Input text to sanitize
        allow_html (bool): Whether to allow HTML tags (default: False)
    
    Returns:
        str: Sanitized text
    """
    if not text:
        return text
    
    if not allow_html:
        # Escape all HTML characters
        text = escape(text)
    
    # Remove any script tags even if HTML is allowed
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove javascript: protocol
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    
    # Remove on* event handlers
    text = re.sub(r'\s*on\w+\s*=', '', text, flags=re.IGNORECASE)
    
    return text


def validate_alphanumeric(text, field_name="Field", allow_underscore=True, allow_space=False):
    """
    Validate that text contains only alphanumeric characters
    
    Args:
        text (str): Text to validate
        field_name (str): Name of field for error message
        allow_underscore (bool): Allow underscore character
        allow_space (bool): Allow space character
    
    Raises:
        ValidationError: If validation fails
    """
    if not text:
        return
    
    allowed_chars = r'a-zA-Z0-9'
    if allow_underscore:
        allowed_chars += '_'
    if allow_space:
        allowed_chars += r'\s'
    
    pattern = f'^[{allowed_chars}]+$'
    
    if not re.match(pattern, text):
        allowed_msg = "letters and numbers"
        if allow_underscore:
            allowed_msg += ", underscores"
        if allow_space:
            allowed_msg += ", and spaces"
        raise ValidationError(f"{field_name} can only contain {allowed_msg}.")


# ============================================
# FILE VALIDATION
# ============================================

ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']
ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.doc', '.docx']
ALLOWED_ALL_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS + ALLOWED_DOCUMENT_EXTENSIONS

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB


def validate_file_upload(file, allowed_extensions=None, max_size=MAX_FILE_SIZE):
    """
    Validate uploaded file for security
    
    Args:
        file (UploadedFile): Django uploaded file object
        allowed_extensions (list): List of allowed file extensions (e.g., ['.pdf', '.jpg'])
        max_size (int): Maximum file size in bytes
    
    Raises:
        ValidationError: If validation fails
    
    Returns:
        bool: True if validation passes
    """
    if not file:
        return True
    
    # Validate file size
    if file.size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise ValidationError(f"File size must be less than {max_size_mb}MB.")
    
    # Validate file extension
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_ALL_EXTENSIONS
    
    file_ext = os.path.splitext(file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        extensions_str = ', '.join(allowed_extensions)
        raise ValidationError(f"Only {extensions_str} files are allowed.")
    
    # Validate file content type
    content_type = file.content_type
    
    # Check for image files
    if file_ext in ALLOWED_IMAGE_EXTENSIONS:
        if not content_type.startswith('image/'):
            raise ValidationError("File content does not match its extension.")
    
    # Check for PDF files
    elif file_ext == '.pdf':
        if content_type not in ['application/pdf', 'application/x-pdf']:
            raise ValidationError("File content does not match PDF format.")
    
    # Check for suspicious file names
    suspicious_patterns = ['..', '~', '/', '\\', '\0']
    for pattern in suspicious_patterns:
        if pattern in file.name:
            raise ValidationError("Invalid file name detected.")
    
    return True


def validate_image_file(file):
    """
    Validate uploaded image file
    
    Args:
        file (UploadedFile): Uploaded image file
    
    Raises:
        ValidationError: If validation fails
    """
    return validate_file_upload(file, ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_SIZE)


def validate_document_file(file):
    """
    Validate uploaded document file
    
    Args:
        file (UploadedFile): Uploaded document file
    
    Raises:
        ValidationError: If validation fails
    """
    return validate_file_upload(file, ALLOWED_DOCUMENT_EXTENSIONS, MAX_FILE_SIZE)


# ============================================
# DATA VALIDATION
# ============================================

def validate_phone_number(phone):
    """
    Validate Indian phone number
    
    Args:
        phone (str): Phone number to validate
    
    Raises:
        ValidationError: If validation fails
    """
    if not phone:
        return
    
    # Remove any spaces or dashes
    phone = phone.replace(' ', '').replace('-', '')
    
    # Check if it's exactly 10 digits
    if not phone.isdigit() or len(phone) != 10:
        raise ValidationError("Phone number must be exactly 10 digits.")
    
    # Check if it starts with valid prefix (6, 7, 8, 9)
    if not phone.startswith(('6', '7', '8', '9')):
        raise ValidationError("Phone number must start with 6, 7, 8, or 9.")


def validate_aadhar_number(aadhar):
    """
    Validate Aadhar number
    
    Args:
        aadhar (str): Aadhar number to validate
    
    Raises:
        ValidationError: If validation fails
    """
    if not aadhar:
        return
    
    # Remove any spaces
    aadhar = aadhar.replace(' ', '')
    
    # Check if it's exactly 12 digits
    if not aadhar.isdigit() or len(aadhar) != 12:
        raise ValidationError("Aadhar number must be exactly 12 digits.")


def validate_pincode(pincode):
    """
    Validate Indian pincode
    
    Args:
        pincode (str): Pincode to validate
    
    Raises:
        ValidationError: If validation fails
    """
    if not pincode:
        return
    
    # Remove any spaces
    pincode = pincode.replace(' ', '')
    
    # Check if it's exactly 6 digits
    if not pincode.isdigit() or len(pincode) != 6:
        raise ValidationError("Pincode must be exactly 6 digits.")


# ============================================
# SQL INJECTION PREVENTION
# ============================================

def is_safe_for_sql(text):
    """
    Check if text is safe for SQL queries (basic check)
    Note: Django ORM already prevents SQL injection, this is an extra layer
    
    Args:
        text (str): Text to check
    
    Returns:
        bool: True if text appears safe
    """
    if not text:
        return True
    
    # Check for common SQL injection patterns
    dangerous_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(;|\-\-|\/\*|\*\/)",  # SQL comment markers
        r"(\bOR\b.*=.*)",  # OR 1=1 pattern
        r"(\bUNION\b.*\bSELECT\b)",  # UNION SELECT
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, str(text), re.IGNORECASE):
            return False
    
    return True


# ============================================
# SECURITY HEADERS HELPER
# ============================================

def get_security_headers():
    """
    Return recommended security headers
    
    Returns:
        dict: Dictionary of security headers
    """
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;",
    }


# ============================================
# RATE LIMITING HELPERS
# ============================================

from django.core.cache import cache
from django.http import HttpResponse


def check_rate_limit(identifier, limit=5, period=60):
    """
    Simple rate limiting check using Django cache
    
    Args:
        identifier (str): Unique identifier (e.g., IP address, user ID)
        limit (int): Maximum number of requests allowed
        period (int): Time period in seconds
    
    Returns:
        bool: True if under limit, False if exceeded
    """
    cache_key = f'rate_limit_{identifier}'
    requests = cache.get(cache_key, 0)
    
    if requests >= limit:
        return False
    
    # Increment counter
    cache.set(cache_key, requests + 1, period)
    return True


def rate_limit_exceeded_response():
    """
    Return HTTP response for rate limit exceeded
    
    Returns:
        HttpResponse: 429 Too Many Requests response
    """
    return HttpResponse(
        "Too many requests. Please try again later.",
        status=429
    )


# ============================================
# PASSWORD STRENGTH CHECKER
# ============================================

def check_password_strength(password):
    """
    Check password strength and return suggestions
    
    Args:
        password (str): Password to check
    
    Returns:
        dict: {
            'is_strong': bool,
            'score': int (0-5),
            'suggestions': list of strings
        }
    """
    score = 0
    suggestions = []
    
    # Check length
    if len(password) >= 8:
        score += 1
    else:
        suggestions.append("Use at least 8 characters")
    
    # Check for uppercase
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        suggestions.append("Add uppercase letters")
    
    # Check for lowercase
    if re.search(r'[a-z]', password):
        score += 1
    else:
        suggestions.append("Add lowercase letters")
    
    # Check for numbers
    if re.search(r'\d', password):
        score += 1
    else:
        suggestions.append("Add numbers")
    
    # Check for special characters
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        suggestions.append("Add special characters (!@#$%^&*)")
    
    return {
        'is_strong': score >= 4,
        'score': score,
        'suggestions': suggestions
    }


# ============================================
# LOGGING HELPERS
# ============================================

import logging

logger = logging.getLogger(__name__)


def log_security_event(event_type, user, details, severity='INFO'):
    """
    Log security-related events
    
    Args:
        event_type (str): Type of event (e.g., 'login_failed', 'unauthorized_access')
        user: User object or username
        details (str): Additional details
        severity (str): 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    """
    username = user.username if hasattr(user, 'username') else str(user)
    
    log_message = f"[SECURITY] {event_type} | User: {username} | {details}"
    
    if severity == 'CRITICAL':
        logger.critical(log_message)
    elif severity == 'ERROR':
        logger.error(log_message)
    elif severity == 'WARNING':
        logger.warning(log_message)
    else:
        logger.info(log_message)


def log_failed_login(username, ip_address):
    """Log failed login attempt"""
    log_security_event(
        'LOGIN_FAILED',
        username,
        f"Failed login from IP: {ip_address}",
        'WARNING'
    )


def log_unauthorized_access(user, attempted_url):
    """Log unauthorized access attempt"""
    log_security_event(
        'UNAUTHORIZED_ACCESS',
        user,
        f"Attempted to access: {attempted_url}",
        'WARNING'
    )


def log_suspicious_activity(user, activity_description):
    """Log suspicious activity"""
    log_security_event(
        'SUSPICIOUS_ACTIVITY',
        user,
        activity_description,
        'ERROR'
    )


# ============================================
# OTP GENERATION & EMAIL VERIFICATION
# ============================================

def generate_otp():
    """
    Generate secure 6-digit OTP
    
    Returns:
        str: 6-digit OTP code
    
    Security:
        - Uses secrets module (cryptographically secure)
        - Generates random 6-digit code (100000-999999)
        - Avoids predictable patterns
    """
    import secrets
    return str(secrets.randbelow(900000) + 100000)


def create_otp_for_user(user):
    """
    Create OTP record for user email verification
    
    Args:
        user: CustomUser instance
    
    Returns:
        EmailOTP: Created OTP instance
    
    Security:
        - Invalidates all previous OTPs for same user
        - Sets 10-minute expiration
        - Logs OTP generation event
    """
    from .models import EmailOTP
    from django.utils import timezone
    from datetime import timedelta
    
    # Invalidate all previous OTPs for this user
    EmailOTP.objects.filter(
        user=user,
        is_verified=False
    ).update(is_used=True)
    
    # Generate new OTP
    otp_code = generate_otp()
    
    # Create OTP record
    otp = EmailOTP.objects.create(
        user=user,
        email=user.email,
        otp_code=otp_code,
        expires_at=timezone.now() + timedelta(minutes=10)
    )
    
    # Log OTP generation
    log_security_event(
        'OTP_GENERATED',
        user.username,
        f"OTP generated for email: {user.email}",
        'INFO'
    )
    
    return otp


def verify_otp(user, otp_code):
    """
    Verify OTP code for user
    
    Args:
        user: CustomUser instance
        otp_code: 6-digit OTP code to verify
    
    Returns:
        tuple: (success: bool, message: str)
    
    Security:
        - Checks OTP validity (expiration, attempts)
        - Increments attempt counter
        - Marks as used after verification
        - Logs all verification attempts
    """
    from .models import EmailOTP
    from django.utils import timezone
    
    try:
        # Get the latest OTP for user
        otp = EmailOTP.objects.filter(
            user=user,
            is_used=False
        ).order_by('-created_at').first()
        
        if not otp:
            log_security_event(
                'OTP_VERIFICATION_FAILED',
                user.username,
                "No valid OTP found",
                'WARNING'
            )
            return False, "No OTP found. Please request a new one."
        
        # Check if OTP is expired
        if timezone.now() > otp.expires_at:
            log_security_event(
                'OTP_EXPIRED',
                user.username,
                f"OTP expired at {otp.expires_at}",
                'WARNING'
            )
            return False, "OTP has expired. Please request a new one."
        
        # Check attempt limit (max 3 attempts)
        if otp.verification_attempts >= 3:
            otp.is_used = True
            otp.save()
            
            log_security_event(
                'OTP_MAX_ATTEMPTS',
                user.username,
                "Maximum verification attempts exceeded",
                'WARNING'
            )
            return False, "Maximum attempts exceeded. Please request a new OTP."
        
        # Increment attempts
        otp.increment_attempts()
        
        # Verify OTP code
        if otp.otp_code == otp_code:
            # Mark OTP as verified
            otp.mark_as_verified()
            
            # Update user email verification
            user.email_verified = True
            user.email_verified_at = timezone.now()

            # Activate only citizens; staff/admin require manual approval
            if user.role == 'citizen':
                user.is_active = True
                activation_msg = "Email verified successfully! You can now login."
            else:
                user.is_active = False
                activation_msg = (
                    "Email verified successfully! Your account is pending administrator approval."
                )

            user.save(update_fields=['email_verified', 'email_verified_at', 'is_active'])
            
            log_security_event(
                'OTP_VERIFIED_SUCCESS',
                user.username,
                f"Email verified successfully: {user.email}",
                'INFO'
            )
            
            return True, activation_msg
        else:
            log_security_event(
                'OTP_VERIFICATION_FAILED',
                user.username,
                f"Invalid OTP code entered (Attempt {otp.verification_attempts}/3)",
                'WARNING'
            )
            
            attempts_left = 3 - otp.verification_attempts
            return False, f"Invalid OTP code. {attempts_left} attempt(s) remaining."
    
    except Exception as e:
        log_security_event(
            'OTP_VERIFICATION_ERROR',
            user.username,
            f"Error during OTP verification: {str(e)}",
            'ERROR'
        )
        return False, "An error occurred during verification. Please try again."


def send_otp_email(user, otp_code):
    """
    Send OTP via email
    
    Args:
        user: CustomUser instance
        otp_code: 6-digit OTP code
    
    Returns:
        bool: True if email sent successfully, False otherwise
    
    Security:
        - Uses Django's email backend
        - Does not expose OTP in logs
        - Includes expiration time in email
    """
    from django.core.mail import send_mail
    from django.conf import settings
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    
    try:
        # Email subject
        subject = f"Email Verification OTP - {settings.PROJECT_NAME if hasattr(settings, 'PROJECT_NAME') else 'Digital Gram Panchayat Portal'}"
        
        # Email body (HTML)
        html_message = render_to_string('portal_app/emails/otp_verification.html', {
            'user': user,
            'otp_code': otp_code,
            'expiry_minutes': 10,
        })
        
        # Plain text version
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        log_security_event(
            'OTP_EMAIL_SENT',
            user.username,
            f"OTP email sent to: {user.email}",
            'INFO'
        )
        
        return True
    
    except Exception as e:
        log_security_event(
            'OTP_EMAIL_FAILED',
            user.username,
            f"Failed to send OTP email: {str(e)}",
            'ERROR'
        )
        return False


def resend_otp(user):
    """
    Resend OTP to user
    
    Args:
        user: CustomUser instance
    
    Returns:
        tuple: (success: bool, message: str)
    
    Security:
        - Rate limits OTP generation (1 per minute)
        - Invalidates previous OTPs
        - Logs resend attempts
    """
    from .models import EmailOTP
    from django.utils import timezone
    from datetime import timedelta
    
    # Check if user recently requested OTP (rate limiting)
    recent_otp = EmailOTP.objects.filter(
        user=user,
        created_at__gte=timezone.now() - timedelta(minutes=1)
    ).first()
    
    if recent_otp:
        log_security_event(
            'OTP_RESEND_RATE_LIMITED',
            user.username,
            "OTP resend attempted too soon",
            'WARNING'
        )
        return False, "Please wait 1 minute before requesting a new OTP."
    
    # Create new OTP
    otp = create_otp_for_user(user)
    
    # Send OTP email
    if send_otp_email(user, otp.otp_code):
        return True, f"A new OTP has been sent to {user.email}"
    else:
        return False, "Failed to send OTP email. Please try again later."

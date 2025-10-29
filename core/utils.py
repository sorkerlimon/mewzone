from django.core.mail import send_mail
from django.conf import settings
import random
import string


def send_otp_email(email, otp_code):
    """Send OTP verification email"""
    subject = 'MewZone - Email Verification Code'
    message = f'Your verification code for MewZone is: {otp_code}\n\nThis code will expire in 10 minutes.'
    
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])


def generate_otp(length=6):
    """Generate random OTP code"""
    return ''.join(random.choices(string.digits, k=length))

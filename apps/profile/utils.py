import secrets
import uuid
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User


def generate_verification_token():
    """Generate a secure URL-safe token for email verification."""
    # Use UUID for better URL compatibility (no special chars)
    return str(uuid.uuid4())


def send_verification_email(user, token, base_url=None):
    """Send email verification link to user."""
    if base_url is None:
        base_url = 'http://localhost:8000'
    verification_link = f"{base_url}/profile/verify-email/{token}/"
    subject = 'Verify Your Email - MyBudget'
    message = f"""
Hello {user.username},

Thank you for registering with MyBudget! Please verify your email address by clicking the link below:

{verification_link}

This link will expire in 24 hours.

If you didn't create this account, please ignore this email.

Best regards,
MyBudget Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def send_password_reset_email(user, token, base_url=None):
    """Send password reset link to user."""
    if base_url is None:
        base_url = 'http://localhost:8000'
    reset_link = f"{base_url}/profile/password-reset/{token}/"
    subject = 'Password Reset - MyBudget'
    message = f"""
Hello {user.username},

We received a request to reset your password. Click the link below to set a new password:

{reset_link}

This link will expire in 24 hours.

If you didn't request a password reset, please ignore this email.

Best regards,
MyBudget Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def create_verification_token_for_user(user):
    """Create and save a verification token for user."""
    token = generate_verification_token()
    profile = user.profile
    profile.email_verification_token = token
    profile.email_verification_token_expires_at = timezone.now() + timedelta(hours=24)
    profile.save()
    return token


def create_password_reset_token_for_user(user):
    """Create and save a password reset token for user."""
    token = generate_verification_token()
    profile = user.profile
    profile.password_reset_token = token
    profile.password_reset_token_expires_at = timezone.now() + timedelta(hours=24)
    profile.save()
    return token

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class UserProfile(models.Model):
    """Extended user profile with email verification support."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, null=True, blank=True, unique=True)
    email_verification_token_expires_at = models.DateTimeField(null=True, blank=True)
    password_reset_token = models.CharField(max_length=255, null=True, blank=True, unique=True)
    password_reset_token_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def is_email_verification_token_valid(self):
        """Check if email verification token is still valid."""
        if not self.email_verification_token or not self.email_verification_token_expires_at:
            return False
        return timezone.now() < self.email_verification_token_expires_at

    def is_password_reset_token_valid(self):
        """Check if password reset token is still valid."""
        if not self.password_reset_token or not self.password_reset_token_expires_at:
            return False
        return timezone.now() < self.password_reset_token_expires_at

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

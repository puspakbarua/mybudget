from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.profile.models import UserProfile
from apps.profile.utils import (
    create_password_reset_token_for_user,
    create_verification_token_for_user,
    generate_verification_token,
    send_password_reset_email,
    send_verification_email,
)


PASSWORD = "MyBudget-Strong-Password-47!"


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AccountUtilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password=PASSWORD,
        )
        UserProfile.objects.create(user=self.user)

    def test_generated_verification_token_is_uuid(self):
        token = generate_verification_token()

        self.assertEqual(len(token), 36)
        self.assertEqual(token.count("-"), 4)

    def test_verification_token_creation_saves_token_and_expiry(self):
        before_creation = timezone.now()

        token = create_verification_token_for_user(self.user)

        profile = self.user.profile
        profile.refresh_from_db()
        self.assertEqual(profile.email_verification_token, token)
        self.assertGreaterEqual(
            profile.email_verification_token_expires_at,
            before_creation + timedelta(hours=24),
        )
        self.assertTrue(profile.is_email_verification_token_valid())

    def test_password_reset_token_creation_saves_token_and_expiry(self):
        before_creation = timezone.now()

        token = create_password_reset_token_for_user(self.user)

        profile = self.user.profile
        profile.refresh_from_db()
        self.assertEqual(profile.password_reset_token, token)
        self.assertGreaterEqual(
            profile.password_reset_token_expires_at,
            before_creation + timedelta(hours=24),
        )
        self.assertTrue(profile.is_password_reset_token_valid())

    def test_send_verification_email_contains_link_and_recipient(self):
        send_verification_email(self.user, "verification-token")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn(
            "http://localhost:8000/profile/verify-email/verification-token/",
            mail.outbox[0].body,
        )

    def test_send_password_reset_email_contains_link_and_recipient(self):
        send_password_reset_email(self.user, "password-token")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn(
            "http://localhost:8000/profile/password-reset/password-token/",
            mail.outbox[0].body,
        )

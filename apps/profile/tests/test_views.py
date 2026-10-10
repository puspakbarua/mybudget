from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.profile.models import UserProfile


PASSWORD = "MyBudget-Strong-Password-47!"


class HomepageAndRoutingTests(TestCase):
    def test_homepage_displays_navigation_to_app_sections(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
        self.assertContains(response, "Welcome to MyBudget")
        self.assertContains(response, reverse("budgets_index"))
        self.assertContains(response, reverse("transactions_index"))

    def test_homepage_shows_profile_icon_only_for_authenticated_users(self):
        anonymous_response = self.client.get(reverse("home"))
        self.assertNotContains(anonymous_response, 'aria-label="Your profile"')

        user = User.objects.create_user(
            username="homeuser",
            email="homeuser@example.com",
            password=PASSWORD,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, 'aria-label="Your profile"')
        self.assertContains(response, f'href="{reverse("profile_detail")}"')
        self.assertNotContains(response, ">Profile</a>")
        self.assertContains(response, reverse("budgets_index"))
        self.assertContains(response, reverse("transactions_index"))


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class RegistrationAndVerificationTests(TestCase):
    def registration_data(self, **overrides):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        data.update(overrides)
        return data

    def test_registration_creates_inactive_account_and_sends_verification_email(self):
        response = self.client.post(
            reverse("profile_register"), self.registration_data()
        )

        user = User.objects.get(username="newuser")
        profile = user.profile
        self.assertRedirects(response, reverse("profile_verify_email_sent"))
        self.assertFalse(user.is_active)
        self.assertFalse(profile.email_verified)
        self.assertTrue(profile.is_email_verification_token_valid())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["newuser@example.com"])
        self.assertIn(profile.email_verification_token, mail.outbox[0].body)

    def test_registration_rejects_duplicate_email_and_username(self):
        User.objects.create_user(
            username="existing", email="existing@example.com", password=PASSWORD
        )

        for data, error in (
            (
                self.registration_data(email="existing@example.com"),
                "Email is already registered.",
            ),
            (
                self.registration_data(username="existing", email="other@example.com"),
                "Username is already taken.",
            ),
        ):
            with self.subTest(error=error):
                response = self.client.post(reverse("profile_register"), data)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, error)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(mail.outbox, [])

    def test_email_verification_activates_account_and_clears_token(self):
        user = User.objects.create_user(
            username="unverified",
            email="unverified@example.com",
            password=PASSWORD,
            is_active=False,
        )
        profile = UserProfile.objects.create(
            user=user,
            email_verification_token="valid-token",
            email_verification_token_expires_at=timezone.now() + timedelta(hours=1),
        )

        response = self.client.get(
            reverse("profile_verify_email", args=["valid-token"])
        )

        user.refresh_from_db()
        profile.refresh_from_db()
        self.assertRedirects(response, reverse("profile_login"))
        self.assertTrue(user.is_active)
        self.assertTrue(profile.email_verified)
        self.assertIsNone(profile.email_verification_token)
        self.assertIsNone(profile.email_verification_token_expires_at)

    def test_invalid_verification_token_redirects_to_login(self):
        response = self.client.get(
            reverse("profile_verify_email", args=["unknown-token"])
        )

        self.assertRedirects(response, reverse("profile_login"))
        self.assertEqual(User.objects.count(), 0)

    def test_expired_verification_token_deletes_unverified_account(self):
        user = User.objects.create_user(
            username="expired",
            email="expired@example.com",
            password=PASSWORD,
            is_active=False,
        )
        UserProfile.objects.create(
            user=user,
            email_verification_token="expired-token",
            email_verification_token_expires_at=timezone.now() - timedelta(seconds=1),
        )

        response = self.client.get(
            reverse("profile_verify_email", args=["expired-token"])
        )

        self.assertRedirects(response, reverse("profile_register"))
        self.assertFalse(User.objects.filter(username="expired").exists())


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class LoginAndProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="activeuser",
            email="active@example.com",
            password=PASSWORD,
        )
        UserProfile.objects.create(user=self.user, email_verified=True)

    def test_login_accepts_username(self):
        response = self.client.post(
            reverse("profile_login"),
            {"username_or_email": "activeuser", "password": PASSWORD},
        )

        self.assertRedirects(response, reverse("profile_detail"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_accepts_email(self):
        response = self.client.post(
            reverse("profile_login"),
            {"username_or_email": "active@example.com", "password": PASSWORD},
        )

        self.assertRedirects(response, reverse("profile_detail"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_rejects_invalid_password(self):
        response = self.client.post(
            reverse("profile_login"),
            {"username_or_email": "activeuser", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username/email or password.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_rejects_unverified_email(self):
        self.user.profile.email_verified = False
        self.user.profile.save()

        response = self.client.post(
            reverse("profile_login"),
            {"username_or_email": "activeuser", "password": PASSWORD},
        )

        self.assertRedirects(response, reverse("profile_login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_authenticated_user_is_redirected_from_login_and_registration(self):
        self.client.force_login(self.user)

        for url_name in ("profile_login", "profile_register"):
            with self.subTest(page=url_name):
                response = self.client.get(reverse(url_name))
                self.assertRedirects(response, reverse("profile_detail"))

    def test_profile_requires_login_and_displays_profile_for_authenticated_user(self):
        response = self.client.get(reverse("profile_detail"))
        self.assertRedirects(
            response,
            f"{reverse('profile_login')}?next={reverse('profile_detail')}",
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("profile_detail"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile/profile.html")
        self.assertEqual(response.context["profile"], self.user.profile)

    def test_profile_creates_missing_profile(self):
        self.user.profile.delete()
        self.client.force_login(self.user)

        response = self.client.get(reverse("profile_detail"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_logout_page_and_post_logout(self):
        self.client.force_login(self.user)

        get_response = self.client.get(reverse("profile_logout"))
        self.assertEqual(get_response.status_code, 200)
        self.assertTemplateUsed(get_response, "profile/logout.html")

        post_response = self.client.post(reverse("profile_logout"))
        self.assertRedirects(post_response, reverse("profile_login"))
        self.assertNotIn("_auth_user_id", self.client.session)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password=PASSWORD,
        )
        UserProfile.objects.create(user=self.user, email_verified=True)

    def test_password_reset_request_sends_email_with_saved_token(self):
        response = self.client.post(
            reverse("profile_password_reset"), {"email": self.user.email}
        )

        self.user.profile.refresh_from_db()
        self.assertRedirects(response, reverse("profile_login"))
        self.assertTrue(self.user.profile.is_password_reset_token_valid())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.user.profile.password_reset_token, mail.outbox[0].body)

    def test_password_reset_request_rejects_unknown_email(self):
        response = self.client.post(
            reverse("profile_password_reset"), {"email": "missing@example.com"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No account found with this email address.")
        self.assertEqual(mail.outbox, [])

    def test_password_reset_confirmation_changes_password_and_clears_token(self):
        self.user.profile.password_reset_token = "reset-token"
        self.user.profile.password_reset_token_expires_at = (
            timezone.now() + timedelta(hours=1)
        )
        self.user.profile.save()
        new_password = "Another-Strong-Password-83!"

        response = self.client.post(
            reverse("profile_password_reset_confirm", args=["reset-token"]),
            {"new_password1": new_password, "new_password2": new_password},
        )

        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertRedirects(response, reverse("profile_login"))
        self.assertTrue(self.user.check_password(new_password))
        self.assertIsNone(self.user.profile.password_reset_token)
        self.assertIsNone(self.user.profile.password_reset_token_expires_at)

    def test_invalid_password_reset_token_redirects_to_request_form(self):
        response = self.client.get(
            reverse("profile_password_reset_confirm", args=["invalid-token"])
        )

        self.assertRedirects(response, reverse("profile_password_reset"))

    def test_expired_password_reset_token_cannot_be_used(self):
        self.user.profile.password_reset_token = "expired-token"
        self.user.profile.password_reset_token_expires_at = (
            timezone.now() - timedelta(seconds=1)
        )
        self.user.profile.save()

        response = self.client.get(
            reverse("profile_password_reset_confirm", args=["expired-token"])
        )

        self.assertRedirects(response, reverse("profile_password_reset"))
        self.assertTrue(self.user.check_password(PASSWORD))

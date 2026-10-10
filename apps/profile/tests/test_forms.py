from django.contrib.auth.models import User
from django.test import TestCase

from apps.profile.forms import (
    EmailAuthenticationForm,
    PasswordResetForm,
    PasswordResetRequestForm,
    RegistrationForm,
)


PASSWORD = "MyBudget-Strong-Password-47!"


class RegistrationFormTests(TestCase):
    def registration_data(self, **overrides):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        data.update(overrides)
        return data

    def test_valid_registration_form_saves_email(self):
        form = RegistrationForm(self.registration_data())

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.email, "newuser@example.com")

    def test_registration_form_rejects_duplicate_email_and_username(self):
        User.objects.create_user(
            username="existing", email="existing@example.com", password=PASSWORD
        )

        duplicate_email = RegistrationForm(
            self.registration_data(email="existing@example.com")
        )
        duplicate_username = RegistrationForm(
            self.registration_data(username="existing", email="other@example.com")
        )

        self.assertFalse(duplicate_email.is_valid())
        self.assertIn("Email is already registered.", duplicate_email.errors["email"])
        self.assertFalse(duplicate_username.is_valid())
        self.assertIn(
            "Username is already taken.", duplicate_username.errors["username"]
        )

    def test_registration_form_rejects_mismatched_passwords(self):
        form = RegistrationForm(self.registration_data(password2="Different-Password"))

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)


class EmailAuthenticationFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="activeuser",
            email="active@example.com",
            password=PASSWORD,
        )

    def test_authentication_form_accepts_username_or_email(self):
        for identifier in ("activeuser", "active@example.com"):
            with self.subTest(identifier=identifier):
                form = EmailAuthenticationForm(
                    {"username_or_email": identifier, "password": PASSWORD}
                )

                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.get_user(), self.user)

    def test_authentication_form_rejects_invalid_credentials(self):
        form = EmailAuthenticationForm(
            {"username_or_email": "activeuser", "password": "wrong-password"}
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            "Invalid username/email or password.", form.non_field_errors()
        )


class PasswordResetFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password=PASSWORD,
        )

    def test_password_reset_request_form_accepts_existing_email(self):
        form = PasswordResetRequestForm({"email": self.user.email})

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.get_user(), self.user)

    def test_password_reset_request_form_rejects_unknown_email(self):
        form = PasswordResetRequestForm({"email": "missing@example.com"})

        self.assertFalse(form.is_valid())
        self.assertIn(
            "No account found with this email address.", form.errors["email"]
        )

    def test_password_reset_form_rejects_mismatched_passwords(self):
        form = PasswordResetForm(
            self.user,
            {
                "new_password1": "First-Strong-Password-45!",
                "new_password2": "Different-Strong-Password-46!",
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("new_password2", form.errors)

from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from apps.bank_accounts.models import Account
from apps.budgets.models import Category
from apps.transactions.models import Transaction


User = get_user_model()


class BankAccountsPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="account-owner",
            email="owner@example.com",
            password="Strong-password-123!",
        )
        self.client.force_login(self.user)

    def test_bank_accounts_route_shows_accounts_and_related_transactions(self):
        account = Account.objects.create(
            user=self.user,
            name="Everyday account",
            account_type="CURRENT",
            opening_balance="1250.00",
        )
        category = Category.objects.create(user=self.user, name="Groceries")
        Transaction.objects.create(
            account=account,
            category=category,
            transaction_date=date(2026, 10, 1),
            description="Weekly shop",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount="42.50",
        )

        response = self.client.get(reverse("bank_accounts_index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bank_accounts/accounts.html")
        self.assertContains(response, "Bank Accounts")
        self.assertContains(response, "Everyday account")
        self.assertContains(response, "Current account")
        self.assertContains(response, "1250.00")
        self.assertContains(response, "Weekly shop")
        self.assertContains(response, "Groceries")
        self.assertContains(response, reverse("home"))

    def test_bank_accounts_page_only_shows_the_signed_in_users_accounts(self):
        other_user = User.objects.create_user(
            username="another-owner",
            email="another@example.com",
            password="Strong-password-123!",
        )
        Account.objects.create(
            user=other_user,
            name="Private account",
            account_type="SAVINGS",
        )

        response = self.client.get(reverse("bank_accounts_index"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Private account")

    def test_bank_accounts_page_requires_authentication(self):
        self.client.logout()

        response = self.client.get(reverse("bank_accounts_index"))

        self.assertRedirects(
            response,
            f"{reverse('profile_login')}?next={reverse('bank_accounts_index')}",
        )

    def test_bank_accounts_page_shows_empty_state(self):
        response = self.client.get(reverse("bank_accounts_index"))

        self.assertContains(response, "You don’t have any bank accounts yet.")


class BankAccountManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="management-owner",
            email="management@example.com",
            password="Strong-password-123!",
        )
        self.client.force_login(self.user)

    def create_account(self, **kwargs):
        return Account.objects.create(
            user=self.user,
            name="Main account",
            account_type="CURRENT",
            **kwargs,
        )

    def test_create_account_assigns_signed_in_user_and_redirects(self):
        response = self.client.post(
            reverse("bank_accounts_create"),
            {
                "name": "New account",
                "account_type": "SAVINGS",
                "currency": "EUR",
                "opening_balance": "50.00",
                "is_active": "on",
            },
        )

        account = Account.objects.get(name="New account")
        self.assertEqual(account.user, self.user)
        self.assertRedirects(response, reverse("bank_accounts_index"))

    def test_create_account_displays_validation_errors(self):
        response = self.client.post(
            reverse("bank_accounts_create"),
            {
                "name": "",
                "account_type": "INVALID",
                "currency": "EURO",
                "opening_balance": "not-a-number",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bank_accounts/account_form.html")
        self.assertEqual(Account.objects.count(), 0)
        self.assertContains(response, "This field is required.")

    def test_create_account_form_uses_bootstrap5_layout(self):
        response = self.client.get(reverse("bank_accounts_create"))

        self.assertContains(response, "Account details")
        self.assertContains(response, "Starting balance")
        self.assertContains(response, 'class="form-check form-switch"')
        self.assertContains(response, 'name="opening_balance"')

    def test_update_account_changes_account(self):
        account = self.create_account()

        response = self.client.post(
            reverse("bank_accounts_update", args=[account.pk]),
            {
                "name": "Updated account",
                "account_type": "SAVINGS",
                "currency": "USD",
                "opening_balance": "75.00",
                "is_active": "on",
            },
        )

        account.refresh_from_db()
        self.assertEqual(account.name, "Updated account")
        self.assertEqual(account.currency, "USD")
        self.assertRedirects(response, reverse("bank_accounts_index"))

    def test_update_form_renders_active_field_as_checkbox(self):
        active_account = self.create_account()
        inactive_account = Account.objects.create(
            user=self.user,
            name="Inactive account",
            account_type="CURRENT",
            is_active=False,
        )

        active_response = self.client.get(
            reverse("bank_accounts_update", args=[active_account.pk])
        )
        inactive_response = self.client.get(
            reverse("bank_accounts_update", args=[inactive_account.pk])
        )

        self.assertContains(active_response, 'type="checkbox"')
        self.assertContains(active_response, 'class="form-check-input"')
        self.assertContains(active_response, 'id="id_is_active" checked')
        self.assertContains(inactive_response, 'type="checkbox"')
        self.assertNotContains(inactive_response, 'id="id_is_active" checked')

    def test_cannot_update_or_delete_another_users_account(self):
        other_user = User.objects.create_user(
            username="management-other",
            email="management-other@example.com",
            password="Strong-password-123!",
        )
        account = Account.objects.create(
            user=other_user,
            name="Private account",
            account_type="SAVINGS",
        )

        update_response = self.client.get(
            reverse("bank_accounts_update", args=[account.pk])
        )
        delete_response = self.client.get(
            reverse("bank_accounts_delete", args=[account.pk])
        )

        self.assertEqual(update_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)

    def test_delete_requires_confirmation_and_removes_account_on_post(self):
        account = self.create_account()

        confirmation = self.client.get(
            reverse("bank_accounts_delete", args=[account.pk])
        )
        response = self.client.post(
            reverse("bank_accounts_delete", args=[account.pk])
        )

        self.assertContains(confirmation, "Are you sure")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Account.objects.filter(pk=account.pk).exists())

    def test_account_with_transactions_cannot_be_deleted(self):
        account = self.create_account()
        Transaction.objects.create(
            account=account,
            transaction_date=date(2026, 10, 1),
            description="Protected transaction",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount="12.00",
        )

        confirmation = self.client.get(
            reverse("bank_accounts_delete", args=[account.pk])
        )
        response = self.client.post(
            reverse("bank_accounts_delete", args=[account.pk])
        )

        self.assertContains(confirmation, "has related transactions")
        self.assertRedirects(response, reverse("bank_accounts_index"))
        self.assertTrue(Account.objects.filter(pk=account.pk).exists())

    def test_account_receiving_a_transfer_cannot_be_deleted(self):
        source = Account.objects.create(
            user=self.user,
            name="Source account",
            account_type="CURRENT",
        )
        destination = Account.objects.create(
            user=self.user,
            name="Destination account",
            account_type="SAVINGS",
        )
        Transaction.objects.create(
            account=source,
            transfer_to_account=destination,
            transaction_date=date(2026, 10, 1),
            description="Transfer",
            transaction_type=Transaction.TransactionType.TRANSFER,
            amount="20.00",
        )

        confirmation = self.client.get(
            reverse("bank_accounts_delete", args=[destination.pk])
        )
        response = self.client.post(
            reverse("bank_accounts_delete", args=[destination.pk])
        )

        self.assertContains(confirmation, "has related transactions")
        self.assertRedirects(response, reverse("bank_accounts_index"))
        self.assertTrue(Account.objects.filter(pk=destination.pk).exists())

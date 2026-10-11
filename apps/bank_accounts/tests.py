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

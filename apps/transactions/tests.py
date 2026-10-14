from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.bank_accounts.models import Account
from apps.budgets.models import Category
from .models import Transaction


User = get_user_model()


class TransactionManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="transaction-owner",
            email="transaction-owner@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)
        self.account = Account.objects.create(
            user=self.user,
            name="Everyday account",
            account_type="CURRENT",
        )
        self.category = Category.objects.create(
            user=self.user,
            name="Groceries",
        )

    def transaction_data(self, **overrides):
        data = {
            "transaction_type": Transaction.TransactionType.EXPENSE,
            "amount": "42.50",
            "description": "Weekly shop",
            "transaction_date": "2026-10-14",
            "account": self.account.pk,
            "category": self.category.pk,
            "transfer_to_account": "",
        }
        data.update(overrides)
        return data

    def test_transaction_list_shows_only_transactions_from_users_accounts(self):
        Transaction.objects.create(
            account=self.account,
            category=self.category,
            transaction_date=date(2026, 10, 14),
            description="Weekly shop",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount="42.50",
        )
        other_user = User.objects.create_user(
            username="other-transaction-owner",
            email="other-transaction-owner@example.com",
            password="test-password",
        )
        other_account = Account.objects.create(
            user=other_user,
            name="Private account",
            account_type="SAVINGS",
        )
        Transaction.objects.create(
            account=other_account,
            transaction_date=date(2026, 10, 14),
            description="Private transaction",
            transaction_type=Transaction.TransactionType.INCOME,
            amount="100.00",
        )

        response = self.client.get(reverse("transactions_index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transactions/index.html")
        self.assertContains(response, "Weekly shop")
        self.assertContains(response, "Groceries")
        self.assertNotContains(response, "Private transaction")
        self.assertContains(response, reverse("transaction_create"))

    def test_transaction_pages_require_authentication(self):
        self.client.logout()

        for route in (
            "transactions_index",
            "transaction_create",
            "transaction_update",
            "transaction_delete",
        ):
            args = [1] if route in ("transaction_update", "transaction_delete") else []
            with self.subTest(route=route):
                route_path = reverse(route, args=args)
                response = self.client.get(route_path)
                self.assertRedirects(
                    response,
                    f"{reverse('profile_login')}?next={route_path}",
                )

    def test_transaction_form_displays_fields_and_defaults_date(self):
        response = self.client.get(reverse("transaction_create"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transactions/transaction_form.html")
        self.assertContains(response, "Save transaction")
        self.assertContains(response, 'name="transaction_type"')
        self.assertContains(response, 'name="amount"')
        self.assertContains(response, 'name="description"')
        self.assertContains(response, 'name="transaction_date"')
        self.assertContains(response, "Everyday account")
        self.assertContains(response, "Groceries")

    def test_create_transaction_saves_and_redirects(self):
        response = self.client.post(
            reverse("transaction_create"),
            self.transaction_data(),
        )

        transaction = Transaction.objects.get(description="Weekly shop")
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.category, self.category)
        self.assertEqual(transaction.amount, Decimal("42.50"))
        self.assertRedirects(response, reverse("transactions_index"))

    def test_create_transfer_requires_another_owned_account(self):
        response = self.client.post(
            reverse("transaction_create"),
            self.transaction_data(
                transaction_type=Transaction.TransactionType.TRANSFER,
                transfer_to_account=self.account.pk,
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose a different account")
        self.assertEqual(Transaction.objects.count(), 0)

    def test_create_transaction_rejects_another_users_account_or_category(self):
        other_user = User.objects.create_user(
            username="foreign-transaction-owner",
            email="foreign-transaction-owner@example.com",
            password="test-password",
        )
        foreign_account = Account.objects.create(
            user=other_user,
            name="Foreign account",
            account_type="SAVINGS",
        )
        foreign_category = Category.objects.create(
            user=other_user,
            name="Foreign category",
        )

        response = self.client.post(
            reverse("transaction_create"),
            self.transaction_data(
                account=foreign_account.pk,
                category=foreign_category.pk,
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_create_transaction_requires_a_transfer_destination(self):
        response = self.client.post(
            reverse("transaction_create"),
            self.transaction_data(
                transaction_type=Transaction.TransactionType.TRANSFER,
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose an account to transfer to.")
        self.assertEqual(Transaction.objects.count(), 0)

    def test_update_transaction_changes_fields_and_redirects(self):
        transaction = Transaction.objects.create(
            account=self.account,
            category=self.category,
            transaction_date=date(2026, 10, 14),
            description="Weekly shop",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount="42.50",
        )
        response = self.client.post(
            reverse("transaction_update", args=[transaction.pk]),
            self.transaction_data(
                transaction_type=Transaction.TransactionType.INCOME,
                amount="250.00",
                description="Refund",
                category="",
            ),
        )

        transaction.refresh_from_db()
        self.assertEqual(transaction.transaction_type, Transaction.TransactionType.INCOME)
        self.assertEqual(transaction.amount, Decimal("250.00"))
        self.assertEqual(transaction.description, "Refund")
        self.assertIsNone(transaction.category)
        self.assertRedirects(response, reverse("transactions_index"))

    def test_update_transaction_displays_validation_errors_without_saving(self):
        transaction = Transaction.objects.create(
            account=self.account,
            category=self.category,
            transaction_date=date(2026, 10, 14),
            description="Weekly shop",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount="42.50",
        )

        response = self.client.post(
            reverse("transaction_update", args=[transaction.pk]),
            self.transaction_data(amount="-1.00"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Amount must be greater than zero.")
        transaction.refresh_from_db()
        self.assertEqual(transaction.description, "Weekly shop")
        self.assertEqual(transaction.amount, Decimal("42.50"))

    def test_update_transaction_keeps_its_existing_inactive_category_available(self):
        self.category.is_active = False
        self.category.save(update_fields=["is_active"])
        transaction = Transaction.objects.create(
            account=self.account,
            category=self.category,
            transaction_date=date(2026, 10, 14),
            description="Weekly shop",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount="42.50",
        )

        response = self.client.get(
            reverse("transaction_update", args=[transaction.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Groceries")

    def test_delete_transaction_requires_confirmation_post(self):
        transaction = Transaction.objects.create(
            account=self.account,
            category=self.category,
            transaction_date=date(2026, 10, 14),
            description="Weekly shop",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount="42.50",
        )

        confirmation = self.client.get(
            reverse("transaction_delete", args=[transaction.pk])
        )

        self.assertEqual(confirmation.status_code, 200)
        self.assertTemplateUsed(
            confirmation,
            "transactions/transaction_confirm_delete.html",
        )
        self.assertTrue(Transaction.objects.filter(pk=transaction.pk).exists())

        response = self.client.post(
            reverse("transaction_delete", args=[transaction.pk])
        )

        self.assertRedirects(response, reverse("transactions_index"))
        self.assertFalse(Transaction.objects.filter(pk=transaction.pk).exists())

    def test_cannot_update_or_delete_another_users_transaction(self):
        other_user = User.objects.create_user(
            username="private-transaction-owner",
            email="private-transaction-owner@example.com",
            password="test-password",
        )
        other_account = Account.objects.create(
            user=other_user,
            name="Private account",
            account_type="SAVINGS",
        )
        transaction = Transaction.objects.create(
            account=other_account,
            transaction_date=date(2026, 10, 14),
            description="Private transaction",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount="10.00",
        )

        for route in ("transaction_update", "transaction_delete"):
            with self.subTest(route=route):
                response = self.client.get(
                    reverse(route, args=[transaction.pk])
                )
                self.assertEqual(response.status_code, 404)

        self.assertTrue(Transaction.objects.filter(pk=transaction.pk).exists())

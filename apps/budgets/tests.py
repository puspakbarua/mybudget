from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.transactions.models import Transaction
from .models import Category, MonthlyBudget


User = get_user_model()


class BudgetAndCategoryPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="budget-owner",
            email="budget-owner@example.com",
            password="Strong-password-123!",
        )
        self.client.force_login(self.user)

    def test_budget_route_shows_users_monthly_budgets(self):
        category = Category.objects.create(user=self.user, name="Groceries")
        MonthlyBudget.objects.create(
            category=category,
            month=date(2026, 10, 1),
            budgeted_amount="350.00",
        )

        response = self.client.get(reverse("budgets_index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "budgets/budget.html")
        self.assertContains(response, "Monthly Budgets")
        self.assertContains(response, "Groceries")
        self.assertContains(response, "October 2026")
        self.assertContains(response, "350.00")
        self.assertContains(response, reverse("categories_index"))
        self.assertContains(response, reverse("home"))

    def test_budget_route_only_shows_the_signed_in_users_data(self):
        other_user = User.objects.create_user(
            username="other-budget-owner",
            email="other-budget-owner@example.com",
            password="Strong-password-123!",
        )
        other_category = Category.objects.create(
            user=other_user,
            name="Private category",
        )
        MonthlyBudget.objects.create(
            category=other_category,
            month=date(2026, 10, 1),
            budgeted_amount="400.00",
        )

        response = self.client.get(reverse("budgets_index"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Private category")
        self.assertNotContains(response, "400.00")

    def test_budget_route_requires_authentication(self):
        self.client.logout()

        response = self.client.get(reverse("budgets_index"))

        self.assertRedirects(
            response,
            f"{reverse('profile_login')}?next={reverse('budgets_index')}",
        )

    def test_budget_page_shows_empty_states(self):
        response = self.client.get(reverse("budgets_index"))

        self.assertContains(response, "No monthly budgets yet.")

    def test_categories_route_shows_owned_categories_only(self):
        Category.objects.create(user=self.user, name="Groceries")
        other_user = User.objects.create_user(
            username="other-category-page-owner",
            email="other-category-page-owner@example.com",
            password="Strong-password-123!",
        )
        Category.objects.create(user=other_user, name="Private category")

        response = self.client.get(reverse("categories_index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "budgets/categories.html")
        self.assertContains(response, "Groceries")
        self.assertNotContains(response, "Private category")
        self.assertContains(response, reverse("budgets_index"))
        self.assertContains(response, reverse("category_create"))

    def test_categories_route_requires_authentication(self):
        self.client.logout()

        response = self.client.get(reverse("categories_index"))

        self.assertRedirects(
            response,
            f"{reverse('profile_login')}?next={reverse('categories_index')}",
        )

    def test_categories_page_shows_empty_state(self):
        response = self.client.get(reverse("categories_index"))

        self.assertContains(response, "No categories yet.")


class CategoryManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="category-owner",
            email="category-owner@example.com",
            password="Strong-password-123!",
        )
        self.client.force_login(self.user)

    def create_category(self, name="Transport", **kwargs):
        return Category.objects.create(user=self.user, name=name, **kwargs)

    def test_create_category_assigns_signed_in_user(self):
        response = self.client.post(
            reverse("category_create"),
            {"name": "Dining", "is_active": "on"},
        )

        category = Category.objects.get(name="Dining")
        self.assertEqual(category.user, self.user)
        self.assertTrue(category.is_active)
        self.assertRedirects(response, reverse("categories_index"))

    def test_create_category_shows_validation_errors(self):
        self.create_category(name="Already used")

        response = self.client.post(
            reverse("category_create"),
            {"name": "Already used", "is_active": "on"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "budgets/category_form.html")
        self.assertContains(response, "Category with this Name already exists.")

    def test_update_category_changes_name_and_active_state(self):
        category = self.create_category()

        response = self.client.post(
            reverse("category_update", args=[category.pk]),
            {"name": "Travel", "is_active": ""},
        )

        category.refresh_from_db()
        self.assertEqual(category.name, "Travel")
        self.assertFalse(category.is_active)
        self.assertRedirects(response, reverse("categories_index"))

    def test_category_update_form_renders_active_checkbox(self):
        category = self.create_category()

        response = self.client.get(reverse("category_update", args=[category.pk]))

        self.assertContains(response, 'type="checkbox"')
        self.assertContains(response, 'class="form-check-input"')
        self.assertContains(response, 'id="id_is_active" checked')

    def test_cannot_update_or_delete_another_users_category(self):
        other_user = User.objects.create_user(
            username="other-category-owner",
            email="other-category-owner@example.com",
            password="Strong-password-123!",
        )
        category = Category.objects.create(user=other_user, name="Private")

        update_response = self.client.get(
            reverse("category_update", args=[category.pk])
        )
        delete_response = self.client.get(
            reverse("category_delete", args=[category.pk])
        )

        self.assertEqual(update_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)

    def test_delete_category_requires_confirmation_and_deletes_on_post(self):
        category = self.create_category()

        confirmation = self.client.get(reverse("category_delete", args=[category.pk]))
        response = self.client.post(reverse("category_delete", args=[category.pk]))

        self.assertContains(confirmation, "Are you sure")
        self.assertRedirects(response, reverse("categories_index"))
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())

    def test_category_used_by_budget_cannot_be_deleted(self):
        category = self.create_category()
        MonthlyBudget.objects.create(
            category=category,
            month=date(2026, 10, 1),
            budgeted_amount="100.00",
        )

        confirmation = self.client.get(reverse("category_delete", args=[category.pk]))
        response = self.client.post(reverse("category_delete", args=[category.pk]))

        self.assertContains(confirmation, "cannot be deleted")
        self.assertRedirects(response, reverse("categories_index"))
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())

    def test_category_used_by_transaction_cannot_be_deleted(self):
        category = self.create_category()
        from apps.bank_accounts.models import Account

        account = Account.objects.create(
            user=self.user,
            name="Transaction account",
            account_type="CURRENT",
        )
        Transaction.objects.create(
            account=account,
            category=category,
            transaction_date=date(2026, 10, 1),
            description="Category reference",
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount="10.00",
        )

        confirmation = self.client.get(reverse("category_delete", args=[category.pk]))
        response = self.client.post(reverse("category_delete", args=[category.pk]))

        self.assertContains(confirmation, "cannot be deleted")
        self.assertRedirects(response, reverse("categories_index"))
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())


class MonthlyBudgetManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="monthly-budget-owner",
            email="monthly-budget-owner@example.com",
            password="Strong-password-123!",
        )
        self.client.force_login(self.user)
        self.category = Category.objects.create(user=self.user, name="Household")

    def create_budget(self, category=None, month=date(2026, 10, 1), amount="200.00"):
        return MonthlyBudget.objects.create(
            category=category or self.category,
            month=month,
            budgeted_amount=amount,
        )

    def test_create_monthly_budget_for_owned_category(self):
        response = self.client.post(
            reverse("monthly_budget_create"),
            {
                "category": self.category.pk,
                "month": "2026-10-01",
                "budgeted_amount": "350.00",
            },
        )

        budget = MonthlyBudget.objects.get(category=self.category)
        self.assertEqual(budget.budgeted_amount, 350)
        self.assertRedirects(response, reverse("budgets_index"))

    def test_monthly_budget_requires_month_start_date(self):
        response = self.client.post(
            reverse("monthly_budget_create"),
            {
                "category": self.category.pk,
                "month": "2026-10-15",
                "budgeted_amount": "350.00",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "budgets/monthly_budget_form.html")
        self.assertContains(response, "Choose the first day of the month.")
        self.assertEqual(MonthlyBudget.objects.count(), 0)

    def test_monthly_budget_amount_must_be_nonnegative(self):
        response = self.client.post(
            reverse("monthly_budget_create"),
            {
                "category": self.category.pk,
                "month": "2026-10-01",
                "budgeted_amount": "-1.00",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MonthlyBudget.objects.count(), 0)
        self.assertContains(response, "Budget amount cannot be negative.")

    def test_category_choices_are_limited_to_signed_in_user(self):
        other_user = User.objects.create_user(
            username="other-monthly-owner",
            email="other-monthly-owner@example.com",
            password="Strong-password-123!",
        )
        Category.objects.create(user=other_user, name="Other category")

        response = self.client.get(reverse("monthly_budget_create"))

        self.assertContains(response, "Household")
        self.assertNotContains(response, "Other category")

    def test_update_monthly_budget(self):
        budget = self.create_budget()

        response = self.client.post(
            reverse("monthly_budget_update", args=[budget.pk]),
            {
                "category": self.category.pk,
                "month": "2026-11-01",
                "budgeted_amount": "275.00",
            },
        )

        budget.refresh_from_db()
        self.assertEqual(budget.month, date(2026, 11, 1))
        self.assertEqual(budget.budgeted_amount, 275)
        self.assertRedirects(response, reverse("budgets_index"))

    def test_cannot_update_or_delete_another_users_budget(self):
        other_user = User.objects.create_user(
            username="other-budget-owner-2",
            email="other-budget-owner-2@example.com",
            password="Strong-password-123!",
        )
        other_category = Category.objects.create(
            user=other_user,
            name="Other household",
        )
        budget = self.create_budget(category=other_category)

        update_response = self.client.get(
            reverse("monthly_budget_update", args=[budget.pk])
        )
        delete_response = self.client.get(
            reverse("monthly_budget_delete", args=[budget.pk])
        )

        self.assertEqual(update_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)

    def test_delete_monthly_budget_requires_confirmation(self):
        budget = self.create_budget()

        confirmation = self.client.get(
            reverse("monthly_budget_delete", args=[budget.pk])
        )
        response = self.client.post(
            reverse("monthly_budget_delete", args=[budget.pk])
        )

        self.assertContains(confirmation, "Are you sure")
        self.assertRedirects(response, reverse("budgets_index"))
        self.assertFalse(MonthlyBudget.objects.filter(pk=budget.pk).exists())

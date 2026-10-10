from django.test import TestCase
from django.urls import reverse


class BudgetLandingPageTests(TestCase):
    def test_budget_route_renders_landing_page(self):
        response = self.client.get(reverse("budgets_index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "budgets/index.html")
        self.assertContains(response, "<h1>Budgets</h1>", html=True)
        self.assertContains(response, "Budget management will be available here.")
        self.assertContains(response, reverse("home"))

from django.test import TestCase
from django.urls import reverse


class TransactionLandingPageTests(TestCase):
    def test_transaction_route_renders_landing_page(self):
        response = self.client.get(reverse("transactions_index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transactions/index.html")
        self.assertContains(response, "<h1>Transactions</h1>", html=True)
        self.assertContains(response, "Transaction tracking will be available here.")
        self.assertContains(response, reverse("home"))

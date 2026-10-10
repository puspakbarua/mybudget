from django.test import TestCase
from django.urls import reverse


class BankAccountsLandingPageTests(TestCase):
    def test_bank_accounts_route_renders_landing_page(self):
        response = self.client.get(reverse("bank_accounts_index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bank_accounts/index.html")
        self.assertContains(response, "<h1>Bank Accounts</h1>", html=True)
        self.assertContains(response, "Bank account management will be available here.")
        self.assertContains(response, reverse("home"))

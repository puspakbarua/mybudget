from django.conf import settings
from django.db import models


class Account(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    account_type = models.CharField(
        max_length=20,
        choices=[
            ("CURRENT", "Current account"),
            ("SAVINGS", "Savings account"),
            ("CASH", "Cash"),
            ("CREDIT_CARD", "Credit card"),
        ],
    )
    currency = models.CharField(max_length=3, default="EUR")
    opening_balance = models.DecimalField(
        max_digits=14, decimal_places=2, default=0
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
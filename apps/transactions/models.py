from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.bank_accounts.models import Account as BankAccount
from apps.budgets.models import Category

# Create your models here.
class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = "INCOME", "Income"
        EXPENSE = "EXPENSE", "Expense"
        TRANSFER = "TRANSFER", "Transfer"

    account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="transactions",
        null=True,
        blank=True,
    )
    transaction_date = models.DateField()
    description = models.CharField(max_length=255)
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
    )
    amount = models.DecimalField(
        max_digits=14, decimal_places=2
    )
    transfer_to_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name="incoming_transfers",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transaction_date", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="transaction_amount_positive",
            ),
        ]

    def __str__(self):
        return (
            f"{self.transaction_date} - "
            f"{self.description} - {self.amount}"
        )
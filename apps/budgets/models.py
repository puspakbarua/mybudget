from django.conf import settings
from django.db import models
from django.db.models import Q


# Create your models here.
class Category(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class MonthlyBudget(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="monthly_budgets",
    )
    month = models.DateField(
        help_text="Use the first day of the month"
    )
    budgeted_amount = models.DecimalField(
        max_digits=14, decimal_places=2
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["category", "month"],
                name="unique_category_month_budget",
            ),
            models.CheckConstraint(
                condition=Q(budgeted_amount__gte=0),
                name="budget_amount_nonnegative",
            ),
        ]
        ordering = ["month", "category__name"]

    def __str__(self):
        return f"{self.category} - {self.month:%Y-%m}"
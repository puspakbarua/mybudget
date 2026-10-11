import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bank_accounts", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.DeleteModel(
            name="Account",
        ),
        migrations.CreateModel(
            name="Account",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                (
                    "account_type",
                    models.CharField(
                        choices=[
                            ("CURRENT", "Current account"),
                            ("SAVINGS", "Savings account"),
                            ("CASH", "Cash"),
                            ("CREDIT_CARD", "Credit card"),
                        ],
                        max_length=20,
                    ),
                ),
                ("currency", models.CharField(default="EUR", max_length=3)),
                (
                    "opening_balance",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=14,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]

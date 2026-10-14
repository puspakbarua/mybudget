from django import forms
from django.db.models import Q
from django.utils import timezone

from apps.bank_accounts.models import Account
from apps.budgets.models import Category
from .models import Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = (
            "transaction_type",
            "amount",
            "description",
            "transaction_date",
            "account",
            "category",
            "transfer_to_account",
        )
        widgets = {
            "transaction_date": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
        }
        labels = {
            "account": "Account",
            "category": "Category",
            "transfer_to_account": "Transfer to",
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        account_filter = Q(user=user, is_active=True)
        category_filter = Q(user=user, is_active=True)
        if self.instance.pk:
            account_filter |= Q(pk=self.instance.account_id, user=user)
            category_filter |= Q(pk=self.instance.category_id, user=user)
            if self.instance.transfer_to_account_id:
                account_filter |= Q(
                    pk=self.instance.transfer_to_account_id,
                    user=user,
                )
        accounts = Account.objects.filter(account_filter).order_by("name")
        self.fields["account"].queryset = accounts
        self.fields["transfer_to_account"].queryset = accounts
        self.fields["category"].queryset = Category.objects.filter(
            category_filter
        ).order_by("name")
        self.fields["category"].required = False
        self.fields["transfer_to_account"].required = False
        self.fields["transaction_date"].initial = timezone.localdate()
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-select"
                if isinstance(field.widget, forms.Select)
                else "form-control"
            )

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get("transaction_type") == Transaction.TransactionType.TRANSFER
            and cleaned_data.get("account")
            and cleaned_data.get("transfer_to_account")
            and cleaned_data["account"] == cleaned_data["transfer_to_account"]
        ):
            self.add_error(
                "transfer_to_account",
                "Choose a different account for the transfer destination.",
            )
        elif (
            cleaned_data.get("transaction_type") == Transaction.TransactionType.TRANSFER
            and not cleaned_data.get("transfer_to_account")
        ):
            self.add_error(
                "transfer_to_account",
                "Choose an account to transfer to.",
            )
        return cleaned_data

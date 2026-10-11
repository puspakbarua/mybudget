from django import forms

from .models import Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ("name", "account_type", "currency", "opening_balance", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-check-input"
                if isinstance(field.widget, forms.CheckboxInput)
                else "form-select"
                if isinstance(field.widget, forms.Select)
                else "form-control"
            )

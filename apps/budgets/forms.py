from django import forms

from .models import Category, MonthlyBudget


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-check-input"
                if isinstance(field.widget, forms.CheckboxInput)
                else "form-control"
            )


class MonthlyBudgetForm(forms.ModelForm):
    class Meta:
        model = MonthlyBudget
        fields = ("category", "month", "budgeted_amount")
        widgets = {
            "month": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(user=user)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-select"
                if isinstance(field.widget, forms.Select)
                else "form-control"
            )

    def clean_month(self):
        month = self.cleaned_data["month"]
        if month.day != 1:
            raise forms.ValidationError("Choose the first day of the month.")
        return month

    def clean_budgeted_amount(self):
        amount = self.cleaned_data["budgeted_amount"]
        if amount < 0:
            raise forms.ValidationError("Budget amount cannot be negative.")
        return amount

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoryForm, MonthlyBudgetForm
from .models import Category, MonthlyBudget


@login_required(login_url="profile_login")
def index(request):
    budgets = (
        MonthlyBudget.objects.filter(category__user=request.user)
        .select_related("category")
    )
    return render(
        request,
        "budgets/budget.html",
        {"budgets": budgets},
    )


@login_required(login_url="profile_login")
def categories_index(request):
    categories = Category.objects.filter(user=request.user).order_by("name")
    return render(
        request,
        "budgets/categories.html",
        {"categories": categories},
    )


@login_required(login_url="profile_login")
def category_create(request):
    form = CategoryForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        category = form.save(commit=False)
        category.user = request.user
        category.save()
        messages.success(request, "Category created.")
        return redirect("categories_index")

    return render(
        request,
        "budgets/category_form.html",
        {"form": form, "title": "Create category"},
    )


@login_required(login_url="profile_login")
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    form = CategoryForm(
        request.POST if request.method == "POST" else None,
        instance=category,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category updated.")
        return redirect("categories_index")

    return render(
        request,
        "budgets/category_form.html",
        {"form": form, "title": "Update category", "category": category},
    )


@login_required(login_url="profile_login")
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    can_delete = not (
        category.transactions.exists() or category.monthly_budgets.exists()
    )
    if request.method == "POST":
        try:
            category.delete()
        except ProtectedError:
            messages.error(
                request,
                "This category cannot be deleted because it is used by a transaction or budget.",
            )
        else:
            messages.success(request, "Category deleted.")
        return redirect("categories_index")

    return render(
        request,
        "budgets/category_confirm_delete.html",
        {"category": category, "can_delete": can_delete},
    )


@login_required(login_url="profile_login")
def monthly_budget_create(request):
    form = MonthlyBudgetForm(
        request.POST if request.method == "POST" else None,
        user=request.user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Monthly budget created.")
        return redirect("budgets_index")

    return render(
        request,
        "budgets/monthly_budget_form.html",
        {"form": form, "title": "Create monthly budget"},
    )


@login_required(login_url="profile_login")
def monthly_budget_update(request, pk):
    monthly_budget = get_object_or_404(
        MonthlyBudget,
        pk=pk,
        category__user=request.user,
    )
    form = MonthlyBudgetForm(
        request.POST if request.method == "POST" else None,
        instance=monthly_budget,
        user=request.user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Monthly budget updated.")
        return redirect("budgets_index")

    return render(
        request,
        "budgets/monthly_budget_form.html",
        {
            "form": form,
            "title": "Update monthly budget",
            "monthly_budget": monthly_budget,
        },
    )


@login_required(login_url="profile_login")
def monthly_budget_delete(request, pk):
    monthly_budget = get_object_or_404(
        MonthlyBudget,
        pk=pk,
        category__user=request.user,
    )
    if request.method == "POST":
        monthly_budget.delete()
        messages.success(request, "Monthly budget deleted.")
        return redirect("budgets_index")

    return render(
        request,
        "budgets/monthly_budget_confirm_delete.html",
        {"monthly_budget": monthly_budget},
    )

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TransactionForm
from .models import Transaction


@login_required(login_url="profile_login")
def index(request):
    transactions = (
        Transaction.objects.filter(account__user=request.user)
        .select_related("account", "category", "transfer_to_account")
    )
    return render(
        request,
        "transactions/index.html",
        {"transactions": transactions},
    )


@login_required(login_url="profile_login")
def transaction_create(request):
    form = TransactionForm(
        request.POST if request.method == "POST" else None,
        user=request.user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Transaction recorded.")
        return redirect("transactions_index")

    return render(
        request,
        "transactions/transaction_form.html",
        {"form": form, "title": "Add transaction"},
    )


@login_required(login_url="profile_login")
def transaction_update(request, pk):
    transaction = get_object_or_404(
        Transaction,
        pk=pk,
        account__user=request.user,
    )
    form = TransactionForm(
        request.POST if request.method == "POST" else None,
        instance=transaction,
        user=request.user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Transaction updated.")
        return redirect("transactions_index")

    return render(
        request,
        "transactions/transaction_form.html",
        {"form": form, "title": "Edit transaction", "transaction": transaction},
    )


@login_required(login_url="profile_login")
def transaction_delete(request, pk):
    transaction = get_object_or_404(
        Transaction,
        pk=pk,
        account__user=request.user,
    )
    if request.method == "POST":
        transaction.delete()
        messages.success(request, "Transaction deleted.")
        return redirect("transactions_index")

    return render(
        request,
        "transactions/transaction_confirm_delete.html",
        {"transaction": transaction},
    )

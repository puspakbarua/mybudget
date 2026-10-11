from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Prefetch
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render


from apps.transactions.models import Transaction
from .forms import AccountForm
from .models import Account


@login_required(login_url="profile_login")
def accounts(request):
    accounts = (
        Account.objects.filter(user=request.user)
        .prefetch_related(
            Prefetch(
                "transactions",
                queryset=Transaction.objects.select_related("category"),
            )
        )
    )
    return render(
        request,
        "bank_accounts/accounts.html",
        {"accounts": accounts},
    )


@login_required(login_url="profile_login")
def account_create(request):
    form = AccountForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        account = form.save(commit=False)
        account.user = request.user
        account.save()
        messages.success(request, "Bank account created.")
        return redirect("bank_accounts_index")

    return render(
        request,
        "bank_accounts/account_form.html",
        {"form": form, "title": "Create bank account"},
    )


@login_required(login_url="profile_login")
def account_update(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    form = AccountForm(
        request.POST if request.method == "POST" else None,
        instance=account,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Bank account updated.")
        return redirect("bank_accounts_index")

    return render(
        request,
        "bank_accounts/account_form.html",
        {"form": form, "title": "Update bank account", "account": account},
    )


@login_required(login_url="profile_login")
def account_delete(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    can_delete = not (
        account.transactions.exists() or account.incoming_transfers.exists()
    )
    if request.method == "POST":
        try:
            account.delete()
        except ProtectedError:
            messages.error(
                request,
                "This account cannot be deleted because it has related transactions.",
            )
        else:
            messages.success(request, "Bank account deleted.")
        return redirect("bank_accounts_index")

    return render(
        request,
        "bank_accounts/account_confirm_delete.html",
        {"account": account, "can_delete": can_delete},
    )

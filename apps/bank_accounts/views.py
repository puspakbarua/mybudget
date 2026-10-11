from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import render


from apps.transactions.models import Transaction
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
    return render(request, "bank_accounts/accounts.html", {"accounts": accounts})

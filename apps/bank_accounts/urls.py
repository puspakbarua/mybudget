from django.urls import path

from .views import account_create, account_delete, account_update, accounts

urlpatterns = [
    path("", accounts, name="bank_accounts_index"),
    path("create/", account_create, name="bank_accounts_create"),
    path("<int:pk>/update/", account_update, name="bank_accounts_update"),
    path("<int:pk>/delete/", account_delete, name="bank_accounts_delete"),
]

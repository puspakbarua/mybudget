from django.urls import path
from .views import accounts

urlpatterns = [
    path("", accounts, name="bank_accounts_index"),
]

from django.urls import path
from .views import index

urlpatterns = [
    path("", index, name="bank_accounts_index"),
]

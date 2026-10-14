from django.urls import path

from .views import (
    index,
    transaction_create,
    transaction_delete,
    transaction_update,
)

urlpatterns = [
    path("", index, name="transactions_index"),
    path("create/", transaction_create, name="transaction_create"),
    path("<int:pk>/update/", transaction_update, name="transaction_update"),
    path("<int:pk>/delete/", transaction_delete, name="transaction_delete"),
]

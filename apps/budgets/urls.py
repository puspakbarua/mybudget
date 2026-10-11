from django.urls import path

from .views import (
    category_create,
    category_delete,
    category_update,
    categories_index,
    index,
    monthly_budget_create,
    monthly_budget_delete,
    monthly_budget_update,
)

urlpatterns = [
    path("", index, name="budgets_index"),
    path("categories/", categories_index, name="categories_index"),
    path("categories/create/", category_create, name="category_create"),
    path("categories/<int:pk>/update/", category_update, name="category_update"),
    path("categories/<int:pk>/delete/", category_delete, name="category_delete"),
    path("monthly/create/", monthly_budget_create, name="monthly_budget_create"),
    path(
        "monthly/<int:pk>/update/",
        monthly_budget_update,
        name="monthly_budget_update",
    ),
    path(
        "monthly/<int:pk>/delete/",
        monthly_budget_delete,
        name="monthly_budget_delete",
    ),
]

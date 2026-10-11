from django.contrib import admin

# Register your models here.
from .models import Category, MonthlyBudget
admin.site.register(Category)
admin.site.register(MonthlyBudget)
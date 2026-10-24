
from django.contrib import admin
from .models import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'month', 'year', 'amount')
    list_filter = ('category', 'month', 'year')
    search_fields = ('user__username', 'category')
    ordering = ('-year', '-month')

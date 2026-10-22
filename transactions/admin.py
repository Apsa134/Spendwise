from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'amount',
        'transaction_type',
        'category',
        'date',
    )
    list_filter = ('transaction_type', 'category', 'date')
    search_fields = ('title', 'user__username', 'description')
    ordering = ('-date',)
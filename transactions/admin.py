from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'transaction_type', 'amount', 'timestamp', 'status')
    list_filter = ('transaction_type', 'status', 'timestamp')
    search_fields = ('account__account_no', 'account__name', 'description')
    date_hierarchy = 'timestamp'

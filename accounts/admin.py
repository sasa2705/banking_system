from django.contrib import admin
from .models import Account, InterestRate

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_no', 'name', 'account_type', 'balance', 'created_date', 'last_updated')
    list_filter = ('account_type', 'created_date')
    search_fields = ('account_no', 'name', 'email', 'mobile')
    readonly_fields = ('created_date', 'last_updated')

@admin.register(InterestRate)
class InterestRateAdmin(admin.ModelAdmin):
    list_display = ('account_type', 'rate')

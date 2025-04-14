from django import forms
from .models import Transaction
from accounts.models import Account
from django.core.exceptions import ValidationError
from decimal import Decimal
from bootstrap_datepicker_plus.widgets import DatePickerInput

class TransactionForm(forms.Form):
    """Form for deposit and withdrawal operations"""
    account_no = forms.IntegerField(label="Account Number")
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            
        # If user is not an admin and has an account, prefill and disable account_no
        if self.user and not self.user.is_admin and hasattr(self.user, 'account'):
            self.fields['account_no'].initial = self.user.account_no
            self.fields['account_no'].widget.attrs.update({'readonly': 'readonly'})
            
    def clean_account_no(self):
        account_no = self.cleaned_data['account_no']
        
        # Check if account exists
        try:
            account = Account.objects.get(account_no=account_no)
        except Account.DoesNotExist:
            raise ValidationError("Account does not exist")
            
        # If user is not an admin, ensure they're accessing their own account
        if self.user and not self.user.is_admin and self.user.account_no != account_no:
            raise ValidationError("You can only perform transactions on your own account")
            
        return account_no

class AdminTransactionForm(forms.ModelForm):
    """Form for creating transactions by admin"""
    TRANSACTION_TYPES = (
        ('Deposit', 'Deposit'),
        ('Withdrawal', 'Withdrawal'),
        ('Transfer', 'Transfer'),
        ('Interest', 'Interest'),
    )
    
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )
    
    transaction_type = forms.ChoiceField(choices=TRANSACTION_TYPES)
    status = forms.ChoiceField(choices=STATUS_CHOICES)
    to_account = forms.ModelChoiceField(
        queryset=Account.objects.all(),
        required=False,
        label="To Account (for Transfers)",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Transaction
        fields = ['account', 'transaction_type', 'amount', 'description', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apply Bootstrap classes
        for field_name, field in self.fields.items():
            css_class = 'form-control'
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = 'form-check-input'
            elif isinstance(field.widget, forms.RadioSelect):
                css_class = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                css_class = 'form-select'
            field.widget.attrs.update({'class': css_class})
    
    def clean(self):
        cleaned_data = super().clean()
        transaction_type = cleaned_data.get('transaction_type')
        to_account = cleaned_data.get('to_account')
        
        # For transfers, to_account is required
        if transaction_type == 'Transfer' and not to_account:
            self.add_error('to_account', "Recipient account is required for transfers")
        
        return cleaned_data

class WithdrawalForm(TransactionForm):
    """Form for withdrawal operations with additional validation"""
    def clean(self):
        cleaned_data = super().clean()
        account_no = cleaned_data.get('account_no')
        amount = cleaned_data.get('amount')
        
        if account_no and amount:
            account = Account.objects.get(account_no=account_no)
            if account.balance < amount:
                raise ValidationError("Insufficient balance")
        
        return cleaned_data

class TransferForm(forms.Form):
    """Form for transfer operations"""
    from_account = forms.IntegerField(label="From Account")
    to_account = forms.IntegerField(label="To Account")
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            
        # If user is not an admin and has an account, prefill and disable from_account
        if self.user and not self.user.is_admin and hasattr(self.user, 'account'):
            self.fields['from_account'].initial = self.user.account_no
            self.fields['from_account'].widget.attrs.update({'readonly': 'readonly'})
    
    def clean(self):
        cleaned_data = super().clean()
        from_account = cleaned_data.get('from_account')
        to_account = cleaned_data.get('to_account')
        amount = cleaned_data.get('amount')
        
        if from_account and to_account and amount:
            # Check if accounts exist
            try:
                source_account = Account.objects.get(account_no=from_account)
            except Account.DoesNotExist:
                raise ValidationError("Source account does not exist")
                
            try:
                destination_account = Account.objects.get(account_no=to_account)
            except Account.DoesNotExist:
                raise ValidationError("Destination account does not exist")
                
            # If user is not an admin, ensure they're accessing their own account
            if self.user and not self.user.is_admin and self.user.account_no != from_account:
                raise ValidationError("You can only transfer from your own account")
                
            # Check sufficient balance
            if source_account.balance < amount:
                raise ValidationError("Insufficient balance")
                
            # Check same account transfer
            if from_account == to_account:
                raise ValidationError("Cannot transfer to the same account")
        
        return cleaned_data

class TransactionHistoryForm(forms.Form):
    """Form for transaction history lookup"""
    account_no = forms.IntegerField(label="Account Number")
    start_date = forms.DateField(
        required=False,
        widget=DatePickerInput(
            options={"format": "MM/DD/YYYY"}
        )
    )
    end_date = forms.DateField(
        required=False,
        widget=DatePickerInput(
            options={"format": "MM/DD/YYYY"}
        )
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            if isinstance(field.widget, DatePickerInput):
                continue
            field.widget.attrs.update({'class': 'form-control'})
            
        # If user is not an admin and has an account, prefill and disable account_no
        if self.user and not self.user.is_admin and hasattr(self.user, 'account'):
            self.fields['account_no'].initial = self.user.account_no
            self.fields['account_no'].widget.attrs.update({'readonly': 'readonly'})
    
    def clean_account_no(self):
        account_no = self.cleaned_data['account_no']
        
        # Check if account exists
        try:
            account = Account.objects.get(account_no=account_no)
        except Account.DoesNotExist:
            raise ValidationError("Account does not exist")
            
        # If user is not an admin, ensure they're accessing their own account
        if self.user and not self.user.is_admin and self.user.account_no != account_no:
            raise ValidationError("You can only view transactions for your own account")
            
        return account_no
            
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date cannot be after end date") 
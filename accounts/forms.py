from django import forms
from .models import Account, InterestRate
from django.core.exceptions import ValidationError
import random

class AccountCreationForm(forms.ModelForm):
    """Form for creating an account for an existing user"""
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    initial_deposit = forms.DecimalField(min_value=0, max_digits=12, decimal_places=2, required=False, help_text="Optional initial deposit amount")
    
    class Meta:
        model = Account
        fields = ('name', 'address', 'kyc', 'mobile', 'email', 'account_type')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            css_class = 'form-control'
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = 'form-check-input'
            elif isinstance(field.widget, forms.RadioSelect):
                css_class = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                css_class = 'form-select'
            field.widget.attrs.update({'class': css_class})
            
    def clean_account_type(self):
        account_type = self.cleaned_data['account_type']
        try:
            InterestRate.objects.get(account_type=account_type)
        except InterestRate.DoesNotExist:
            raise ValidationError("Selected account type does not exist")
        return account_type
        
class AccountLookupForm(forms.Form):
    """Form for looking up account information"""
    account_no = forms.IntegerField(label="Account Number")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account_no'].widget.attrs.update({'class': 'form-control'})
        
    def clean_account_no(self):
        account_no = self.cleaned_data['account_no']
        try:
            Account.objects.get(account_no=account_no)
        except Account.DoesNotExist:
            raise ValidationError("Account does not exist")
        return account_no 
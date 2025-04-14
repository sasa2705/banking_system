from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from .models import User
from accounts.models import Account, InterestRate
import random
from django.db import transaction

class CustomAuthenticationForm(AuthenticationForm):
    """Custom authentication form with Bootstrap classes"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})
        
class UserRegistrationForm(UserCreationForm):
    """Form for user registration with account creation"""
    name = forms.CharField(max_length=100)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    kyc = forms.CharField(max_length=50, label="KYC ID")
    mobile = forms.CharField(max_length=15)
    email = forms.EmailField()
    account_type = forms.ChoiceField(choices=Account.ACCOUNT_TYPES)
    
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'name', 'address', 'kyc', 
                  'mobile', 'email', 'account_type')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes to all form widgets
        for field_name, field in self.fields.items():
            css_class = 'form-control'
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = 'form-check-input'
            elif isinstance(field.widget, forms.RadioSelect):
                css_class = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                css_class = 'form-select'
            field.widget.attrs.update({'class': css_class})
    
    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Generate account number
        account_no = random.randint(100000, 999999)
        
        # Get interest rate
        interest_rate = InterestRate.objects.get(account_type=self.cleaned_data['account_type'])
        
        # Create account
        account = Account(
            account_no=account_no,
            name=self.cleaned_data['name'],
            address=self.cleaned_data['address'],
            kyc=self.cleaned_data['kyc'],
            mobile=self.cleaned_data['mobile'],
            email=self.cleaned_data['email'],
            account_type=self.cleaned_data['account_type'],
            interest_rate=interest_rate.rate
        )
        
        if commit:
            user.save()
            account.user = user
            account.save()
            user.account_no = account_no
            user.save()
            
        return user

class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with Bootstrap classes"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'}) 
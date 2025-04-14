from django.db import models
from django.utils import timezone
from authentication.models import User

class InterestRate(models.Model):
    """Model to store interest rates for different account types"""
    ACCOUNT_TYPES = [
        ('Savings', 'Savings'),
        ('Current', 'Current'),
        ('Deposit', 'Deposit'),
    ]
    
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, unique=True)
    rate = models.FloatField(help_text="Interest rate in percentage")
    
    def __str__(self) -> str:
        return f"{self.account_type} - {self.rate}%"
        
class Account(models.Model):
    """Model to store bank account information"""
    ACCOUNT_TYPES = [
        ('Savings', 'Savings'),
        ('Current', 'Current'),
        ('Deposit', 'Deposit'),
    ]
    
    account_no = models.IntegerField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account', null=True)
    name = models.CharField(max_length=100)
    address = models.TextField()
    kyc = models.CharField(max_length=50, help_text="KYC identification")
    mobile = models.CharField(max_length=15)
    email = models.EmailField()
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_rate = models.FloatField(help_text="Interest rate for this account")
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return f"{self.account_no} - {self.name}"
        
    def calculate_interest(self) -> float:
        """Calculate monthly interest based on current balance and interest rate"""
        return float(self.balance) * (self.interest_rate / 100)
        
    def get_account_summary(self):
        """Get account summary including transaction count"""
        transaction_count = self.transactions.count()
        last_transaction = self.transactions.order_by('-timestamp').first()
        
        return {
            'account_no': self.account_no,
            'name': self.name,
            'account_type': self.account_type,
            'balance': self.balance,
            'interest_rate': self.interest_rate,
            'transaction_count': transaction_count,
            'last_transaction': last_transaction.timestamp if last_transaction else None,
        }

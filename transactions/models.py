from django.db import models
from django.utils import timezone
from accounts.models import Account

class Transaction(models.Model):
    """Model to store transaction details"""
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('TRANSFER_OUT', 'Transfer Out'),
        ('TRANSFER_IN', 'Transfer In'),
    ]
    
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('PENDING', 'Pending'),
        ('FAILED', 'Failed'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='SUCCESS')
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self) -> str:
        return f"{self.transaction_type} of {self.amount} on {self.timestamp.strftime('%Y-%m-%d')}"

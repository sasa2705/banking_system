from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import Account
from transactions.models import Transaction
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta

@login_required
def dashboard_view(request):
    """Main dashboard view - redirects to appropriate dashboard based on user type"""
    if request.user.is_admin:
        return admin_dashboard(request)
    else:
        return user_dashboard(request)

@login_required
def user_dashboard(request):
    """Dashboard view for regular users"""
    try:
        # Get user's account
        account = request.user.account
        
        # Calculate interest
        interest = account.calculate_interest()
        
        # Get recent transactions (last 5)
        recent_transactions = account.transactions.all()[:5]
        
        context = {
            'account': account,
            'interest': interest,
            'recent_transactions': recent_transactions,
        }
        
        return render(request, 'dashboard/user_dashboard.html', context)
    except Account.DoesNotExist:
        return render(request, 'dashboard/no_account.html')

@login_required
def admin_dashboard(request):
    """Dashboard view for admin users"""
    if not request.user.is_admin:
        return user_dashboard(request)
        
    # Total accounts
    total_accounts = Account.objects.count()
    
    # Total balance
    total_balance = Account.objects.aggregate(Sum('balance'))['balance__sum'] or 0
    
    # Total transactions
    total_transactions = Transaction.objects.count()
    
    # Today's transactions
    today = timezone.now().date()
    today_transactions = Transaction.objects.filter(timestamp__date=today)
    
    # This month's transactions
    first_day_of_month = today.replace(day=1)
    monthly_transactions = Transaction.objects.filter(
        timestamp__date__gte=first_day_of_month,
        timestamp__date__lte=today
    )
    
    # Account type distribution
    account_types = Account.objects.values('account_type').annotate(
        count=Count('account_type')
    ).order_by('account_type')
    
    context = {
        'total_accounts': total_accounts,
        'total_balance': total_balance,
        'total_transactions': total_transactions,
        'today_transactions': today_transactions,
        'monthly_transactions': monthly_transactions,
        'account_types': account_types,
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)

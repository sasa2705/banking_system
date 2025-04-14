from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Account, InterestRate
from .forms import AccountCreationForm, AccountLookupForm
from authentication.models import User
from django.contrib.auth.hashers import check_password
import random
from transactions.models import Transaction

@login_required
def account_detail_view(request, account_no=None):
    """View for displaying account details"""
    user = request.user
    
    # If account_no is not provided, try to get the user's account
    if account_no is None and hasattr(user, 'account'):
        account = user.account
    elif account_no and (user.is_admin or (hasattr(user, 'account') and user.account.account_no == account_no)):
        account = get_object_or_404(Account, account_no=account_no)
    else:
        messages.error(request, "You do not have permission to view this account.")
        return redirect('dashboard')
    
    # Get account summary including transaction count
    account_summary = account.get_account_summary()
    
    # Calculate monthly interest
    monthly_interest = account.calculate_interest()
    
    context = {
        'account': account,
        'account_summary': account_summary,
        'monthly_interest': monthly_interest,
    }
    
    return render(request, 'accounts/account_detail.html', context)

@login_required
def create_account_view(request):
    """View for creating a new account (admin only)"""
    if not request.user.is_admin:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AccountCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            initial_deposit = form.cleaned_data.get('initial_deposit', 0)
            
            # Check if user exists and authenticate
            try:
                user = User.objects.get(username=username)
                if not check_password(password, user.password):
                    messages.error(request, "Invalid username or password.")
                    return render(request, 'accounts/create_account.html', {'form': form})
            except User.DoesNotExist:
                # Create new user if not exists
                user = User.objects.create_user(username=username, password=password)
            
            # Check if user already has an account
            if hasattr(user, 'account'):
                messages.error(request, "User already has an account.")
                return render(request, 'accounts/create_account.html', {'form': form})
            
            try:
                with transaction.atomic():
                    # Generate account number
                    account_no = random.randint(100000, 999999)
                    
                    # Get interest rate
                    interest_rate = InterestRate.objects.get(
                        account_type=form.cleaned_data['account_type']
                    )
                    
                    # Create account
                    account = form.save(commit=False)
                    account.account_no = account_no
                    account.interest_rate = interest_rate.rate
                    account.user = user
                    
                    # Add initial deposit if provided
                    if initial_deposit and initial_deposit > 0:
                        account.balance = initial_deposit
                    
                    account.save()
                    
                    # Create initial deposit transaction if needed
                    if initial_deposit and initial_deposit > 0:
                        Transaction.objects.create(
                            account=account,
                            transaction_type='Deposit',
                            amount=initial_deposit,
                            description=f"Initial deposit on account creation",
                            status='Completed'
                        )
                    
                    # Update user with account number
                    user.account_no = account_no
                    user.save()
                    
                messages.success(request, f"Account created successfully! Account number: {account_no}")
                return redirect('admin_accounts')
            except Exception as e:
                messages.error(request, f"Error creating account: {str(e)}")
    else:
        form = AccountCreationForm()
    
    return render(request, 'accounts/create_account.html', {'form': form})

@login_required
def account_lookup_view(request):
    """View for looking up account information (admin only)"""
    if not request.user.is_admin:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('dashboard')
    
    account = None
    
    if request.method == 'POST':
        form = AccountLookupForm(request.POST)
        if form.is_valid():
            account_no = form.cleaned_data['account_no']
            return redirect('account_detail', account_no=account_no)
    else:
        form = AccountLookupForm()
    
    return render(request, 'accounts/account_lookup.html', {'form': form, 'account': account})

@login_required
def admin_accounts_view(request):
    """View listing all accounts (admin only)"""
    if not request.user.is_admin:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('dashboard')
    
    accounts = Account.objects.all().order_by('-created_date')
    
    return render(request, 'accounts/admin_accounts.html', {'accounts': accounts})

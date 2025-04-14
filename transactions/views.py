from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from .models import Transaction
from .forms import TransactionForm, WithdrawalForm, TransferForm, TransactionHistoryForm, AdminTransactionForm
from accounts.models import Account
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from io import BytesIO
import base64
from datetime import timedelta
import numpy as np

@login_required
def deposit_view(request):
    """View for handling deposits"""
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            account_no = form.cleaned_data['account_no']
            amount = form.cleaned_data['amount']
            
            try:
                with transaction.atomic():
                    account = Account.objects.get(account_no=account_no)
                    
                    # Update account balance
                    account.balance += amount
                    account.last_updated = timezone.now()
                    account.save()
                    
                    # Record transaction
                    Transaction.objects.create(
                        account=account,
                        transaction_type='DEPOSIT',
                        amount=amount,
                        status='SUCCESS',
                        description='Cash deposit'
                    )
                    
                messages.success(request, f"Successfully deposited ₹{amount} to account {account_no}")
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Error processing deposit: {str(e)}")
    else:
        form = TransactionForm(user=request.user)
    
    return render(request, 'transactions/deposit.html', {'form': form})

@login_required
def withdrawal_view(request):
    """View for handling withdrawals"""
    if request.method == 'POST':
        form = WithdrawalForm(request.POST, user=request.user)
        if form.is_valid():
            account_no = form.cleaned_data['account_no']
            amount = form.cleaned_data['amount']
            
            try:
                with transaction.atomic():
                    account = Account.objects.get(account_no=account_no)
                    
                    # Update account balance
                    account.balance -= amount
                    account.last_updated = timezone.now()
                    account.save()
                    
                    # Record transaction
                    Transaction.objects.create(
                        account=account,
                        transaction_type='WITHDRAWAL',
                        amount=-amount,  # Negative amount for withdrawal
                        status='SUCCESS',
                        description='Cash withdrawal'
                    )
                    
                messages.success(request, f"Successfully withdrew ₹{amount} from account {account_no}")
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Error processing withdrawal: {str(e)}")
    else:
        form = WithdrawalForm(user=request.user)
    
    return render(request, 'transactions/withdrawal.html', {'form': form})

@login_required
def transfer_view(request):
    """View for handling transfers between accounts"""
    if request.method == 'POST':
        form = TransferForm(request.POST, user=request.user)
        if form.is_valid():
            from_account_no = form.cleaned_data['from_account']
            to_account_no = form.cleaned_data['to_account']
            amount = form.cleaned_data['amount']
            
            try:
                with transaction.atomic():
                    from_account = Account.objects.get(account_no=from_account_no)
                    to_account = Account.objects.get(account_no=to_account_no)
                    
                    # Update source account
                    from_account.balance -= amount
                    from_account.last_updated = timezone.now()
                    from_account.save()
                    
                    # Update destination account
                    to_account.balance += amount
                    to_account.last_updated = timezone.now()
                    to_account.save()
                    
                    # Record transactions
                    timestamp = timezone.now()
                    
                    # Source transaction
                    Transaction.objects.create(
                        account=from_account,
                        transaction_type='TRANSFER_OUT',
                        amount=-amount,  # Negative amount for outgoing transfer
                        timestamp=timestamp,
                        status='SUCCESS',
                        description=f"Transfer to account {to_account_no}"
                    )
                    
                    # Destination transaction
                    Transaction.objects.create(
                        account=to_account,
                        transaction_type='TRANSFER_IN',
                        amount=amount,
                        timestamp=timestamp,
                        status='SUCCESS',
                        description=f"Transfer from account {from_account_no}"
                    )
                    
                messages.success(request, f"Successfully transferred ₹{amount} from account {from_account_no} to {to_account_no}")
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Error processing transfer: {str(e)}")
    else:
        form = TransferForm(user=request.user)
    
    return render(request, 'transactions/transfer.html', {'form': form})

@login_required
def transaction_history_view(request):
    """View for displaying transaction history"""
    transactions = None
    plot_div = None
    
    if request.method == 'POST':
        form = TransactionHistoryForm(request.POST, user=request.user)
        if form.is_valid():
            account_no = form.cleaned_data['account_no']
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            
            account = get_object_or_404(Account, account_no=account_no)
            
            # Build query
            query = Q(account=account)
            if start_date:
                query &= Q(timestamp__date__gte=start_date)
            if end_date:
                query &= Q(timestamp__date__lte=end_date)
                
            transactions = Transaction.objects.filter(query).order_by('-timestamp')
            
            # Generate plot if transactions exist
            if transactions.exists():
                plot_div = generate_transaction_plot(transactions, account)
    else:
        form = TransactionHistoryForm(user=request.user)
        
        # If user is not admin and has account, show their transactions by default
        if not request.user.is_admin and hasattr(request.user, 'account'):
            account = request.user.account
            transactions = account.transactions.all().order_by('-timestamp')
            
            if transactions.exists():
                plot_div = generate_transaction_plot(transactions, account)
    
    return render(request, 'transactions/transaction_history.html', {
        'form': form,
        'transactions': transactions,
        'plot_div': plot_div
    })

@login_required
def admin_transactions_view(request):
    """View listing all transactions (admin only)"""
    if not request.user.is_admin:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('dashboard')
    
    # Get query parameters for filtering
    account_no = request.GET.get('account_no')
    transaction_type = request.GET.get('transaction_type')
    status = request.GET.get('status')
    
    # Start with all transactions
    transactions = Transaction.objects.all().order_by('-timestamp')
    
    # Apply filters if provided
    if account_no:
        try:
            account = Account.objects.get(account_no=account_no)
            transactions = transactions.filter(account=account)
        except Account.DoesNotExist:
            pass
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
        
    if status:
        transactions = transactions.filter(status=status)
    
    return render(request, 'transactions/admin_transactions.html', {'transactions': transactions})

@login_required
def transaction_detail_view(request, transaction_id):
    """View for displaying transaction details"""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Check permissions
    if not request.user.is_admin and (not hasattr(request.user, 'account') or request.user.account != transaction.account):
        messages.error(request, "You do not have permission to view this transaction.")
        return redirect('dashboard')
    
    return render(request, 'transactions/transaction_detail.html', {'transaction': transaction})

@login_required
def create_transaction_view(request):
    """View for creating a new transaction (admin only)"""
    if not request.user.is_admin:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AdminTransactionForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    new_transaction = form.save(commit=False)
                    account = new_transaction.account
                    to_account = form.cleaned_data.get('to_account')
                    
                    # Process transaction based on type and status
                    if new_transaction.status == 'Completed':
                        if new_transaction.transaction_type == 'Deposit':
                            account.balance += new_transaction.amount
                        elif new_transaction.transaction_type == 'Withdrawal':
                            if account.balance >= new_transaction.amount:
                                account.balance -= new_transaction.amount
                            else:
                                messages.error(request, "Insufficient funds for withdrawal.")
                                raise ValueError("Insufficient funds")
                        elif new_transaction.transaction_type == 'Transfer':
                            if not to_account:
                                messages.error(request, "Recipient account is required for transfers.")
                                raise ValueError("Missing recipient account")
                                
                            if account.balance >= new_transaction.amount:
                                account.balance -= new_transaction.amount
                                to_account.balance += new_transaction.amount
                                to_account.save()
                                
                                # Create corresponding transaction for recipient
                                Transaction.objects.create(
                                    account=to_account,
                                    transaction_type='Transfer',
                                    amount=new_transaction.amount,
                                    status='Completed',
                                    description=f"Transfer from account {account.account_no}",
                                )
                            else:
                                messages.error(request, "Insufficient funds for transfer.")
                                raise ValueError("Insufficient funds")
                    
                    account.save()
                    new_transaction.save()
                    
                    messages.success(request, "Transaction created successfully.")
                    return redirect('admin_transactions')
            except Exception as e:
                messages.error(request, f"Error creating transaction: {str(e)}")
    else:
        form = AdminTransactionForm()
    
    return render(request, 'transactions/create_transaction.html', {'form': form})

@login_required
def approve_transaction_view(request, transaction_id):
    """View for approving a pending transaction"""
    if not request.user.is_admin:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('dashboard')
    
    transaction_obj = get_object_or_404(Transaction, id=transaction_id, status='Pending')
    
    try:
        with transaction.atomic():
            account = transaction_obj.account
            
            # Process based on transaction type
            if transaction_obj.transaction_type == 'Deposit':
                account.balance += transaction_obj.amount
            elif transaction_obj.transaction_type == 'Withdrawal':
                if account.balance >= transaction_obj.amount:
                    account.balance -= transaction_obj.amount
                else:
                    messages.error(request, "Insufficient funds to approve this withdrawal.")
                    return redirect('transaction_detail', transaction_id=transaction_id)
            elif transaction_obj.transaction_type == 'Transfer':
                to_account = transaction_obj.to_account
                if not to_account:
                    messages.error(request, "Transfer recipient account not found.")
                    return redirect('transaction_detail', transaction_id=transaction_id)
                    
                if account.balance >= transaction_obj.amount:
                    account.balance -= transaction_obj.amount
                    to_account.balance += transaction_obj.amount
                    to_account.save()
                else:
                    messages.error(request, "Insufficient funds to approve this transfer.")
                    return redirect('transaction_detail', transaction_id=transaction_id)
            
            # Update transaction status
            transaction_obj.status = 'Completed'
            transaction_obj.save()
            account.save()
            
            messages.success(request, "Transaction approved successfully.")
    except Exception as e:
        messages.error(request, f"Error approving transaction: {str(e)}")
    
    return redirect('transaction_detail', transaction_id=transaction_id)

@login_required
def reject_transaction_view(request, transaction_id):
    """View for rejecting a pending transaction"""
    if not request.user.is_admin:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('dashboard')
    
    transaction_obj = get_object_or_404(Transaction, id=transaction_id, status='Pending')
    
    try:
        # Update transaction status to Failed
        transaction_obj.status = 'Failed'
        transaction_obj.save()
        messages.success(request, "Transaction rejected successfully.")
    except Exception as e:
        messages.error(request, f"Error rejecting transaction: {str(e)}")
    
    return redirect('transaction_detail', transaction_id=transaction_id)

def generate_transaction_plot(transactions, account):
    """Generate transaction history plot"""
    try:
        # Sort by timestamp (oldest first)
        transactions = sorted(transactions, key=lambda x: x.timestamp)
        
        # Extract dates and amounts
        dates = [t.timestamp for t in transactions]
        amounts = [float(t.amount) for t in transactions]
        
        # Calculate running balance
        current_balance = float(account.balance)
        balance_at_end = current_balance
        
        # Work backwards to find the starting balance
        for amount in reversed(amounts):
            balance_at_end -= amount
            
        # Calculate running balance from start to end
        running_balance = [balance_at_end]
        for amount in amounts:
            running_balance.append(running_balance[-1] + amount)
            
        # Remove the first element (it was just to initialize the calculation)
        running_balance.pop(0)
        
        # Create figure and axis
        plt.figure(figsize=(10, 5))
        
        # Plot transaction amounts
        plt.subplot(2, 1, 1)
        colors = ['g' if amount > 0 else 'r' for amount in amounts]
        plt.bar(range(len(amounts)), amounts, color=colors)
        plt.title('Transaction Amounts')
        plt.xticks(range(len(dates)), [d.strftime('%Y-%m-%d') for d in dates], rotation=45)
        plt.tight_layout()
        
        # Plot running balance
        plt.subplot(2, 1, 2)
        plt.plot(range(len(running_balance)), running_balance, 'b-')
        plt.title('Account Balance')
        plt.xticks(range(len(dates)), [d.strftime('%Y-%m-%d') for d in dates], rotation=45)
        plt.tight_layout()
        
        # Save plot to a temporary buffer
        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        
        # Encode the image to base64
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        buf.close()
        
        # Create HTML div with the image
        plot_div = f'<img src="data:image/png;base64,{image_base64}" class="img-fluid">'
        
        return plot_div
    except Exception as e:
        return f"<div class='alert alert-warning'>Could not generate plot: {str(e)}</div>"

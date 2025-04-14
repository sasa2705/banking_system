import os
import django
import random
from django.contrib.auth.hashers import make_password

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'banking_system.settings')
django.setup()

# Import models after Django setup
from authentication.models import User
from accounts.models import Account, InterestRate
from transactions.models import Transaction
from django.utils import timezone
from datetime import timedelta

def create_admin_user():
    """Create default admin user"""
    print("Creating admin user...")
    
    # Check if admin user already exists
    if User.objects.filter(username='admin').exists():
        print("Admin user already exists. Skipping.")
        return User.objects.get(username='admin')
    
    # Create admin user
    admin = User.objects.create(
        username='admin',
        password=make_password('admin123'),
        is_admin=True,
        is_staff=True,
        is_superuser=True
    )
    print(f"Admin user created with username: 'admin' and password: 'admin123'")
    return admin

def create_interest_rates():
    """Create default interest rates"""
    print("Creating interest rates...")
    
    # Check if interest rates already exist
    if InterestRate.objects.exists():
        print("Interest rates already exist. Skipping.")
        return
    
    # Create interest rates
    rates = [
        ('Savings', 4.0),
        ('Current', 0.0),
        ('Deposit', 6.5)
    ]
    
    for account_type, rate in rates:
        InterestRate.objects.create(account_type=account_type, rate=rate)
        print(f"Created interest rate for {account_type}: {rate}%")

def create_demo_accounts():
    """Create demo accounts with users"""
    print("Creating demo accounts...")
    
    # Create demo users and accounts
    for i in range(1, 4):
        username = f"user{i}"
        
        # Skip if user already exists
        if User.objects.filter(username=username).exists():
            print(f"User {username} already exists. Skipping.")
            continue
        
        # Generate account number
        account_no = random.randint(100000, 999999)
        
        # Create user
        user = User.objects.create(
            username=username,
            password=make_password('password123'),
            is_admin=False,
            account_no=account_no
        )
        
        # Get interest rate
        interest_rate = InterestRate.objects.get(account_type='Savings')
        
        # Create account
        account = Account.objects.create(
            account_no=account_no,
            user=user,
            name=f"Demo User {i}",
            address=f"123 Demo St, Demo City",
            kyc=f"KYC{i}12345",
            mobile=f"987654321{i}",
            email=f"user{i}@example.com",
            account_type='Savings',
            balance=1000.00 * i,
            interest_rate=interest_rate.rate,
            created_date=timezone.now() - timedelta(days=i*10)
        )
        
        print(f"Created user {username} with account {account_no}")
        
        # Create initial deposit transaction
        Transaction.objects.create(
            account=account,
            transaction_type='DEPOSIT',
            amount=1000.00 * i,
            timestamp=account.created_date,
            status='SUCCESS',
            description='Initial deposit'
        )
        
        print(f"Created initial deposit transaction for account {account_no}")

def create_demo_transactions():
    """Create demo transactions for accounts"""
    print("Creating demo transactions...")
    
    accounts = Account.objects.all()
    if not accounts:
        print("No accounts found. Skipping transaction creation.")
        return
    
    transaction_types = ['DEPOSIT', 'WITHDRAWAL', 'TRANSFER_IN', 'TRANSFER_OUT']
    
    for account in accounts:
        # Create random transactions for each account
        for i in range(5):
            transaction_type = random.choice(transaction_types)
            
            if transaction_type in ['DEPOSIT', 'TRANSFER_IN']:
                amount = random.randint(100, 500)
            else:
                amount = -random.randint(50, 200)
            
            days_ago = random.randint(1, 30)
            timestamp = timezone.now() - timedelta(days=days_ago)
            
            Transaction.objects.create(
                account=account,
                transaction_type=transaction_type,
                amount=amount,
                timestamp=timestamp,
                status='SUCCESS',
                description=f'Demo {transaction_type.lower().replace("_", " ")}'
            )
        
        print(f"Created 5 random transactions for account {account.account_no}")

def main():
    """Main function to initialize database"""
    print("Initializing database with default data...")
    
    # Create admin user
    admin = create_admin_user()
    
    # Create interest rates
    create_interest_rates()
    
    # Create demo accounts
    create_demo_accounts()
    
    # Create demo transactions
    create_demo_transactions()
    
    print("Database initialization complete!")

if __name__ == "__main__":
    main() 
import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import hashlib
import os
from tkinter import simpledialog
from tkcalendar import DateEntry

# Database Setup
class BankDB:
    def __init__(self):
        self.conn = sqlite3.connect("bank.db")
        self.cursor = self.conn.cursor()
        self.setup_tables()
    
    def setup_tables(self):
        # Admin table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS admin (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL)''')
            
        # Users table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            account_no INTEGER,
            FOREIGN KEY (account_no) REFERENCES accounts (account_no))''')
            
        # Drop existing accounts table if it exists
        self.cursor.execute("DROP TABLE IF EXISTS accounts")
            
        # Accounts table with enhanced fields
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
            account_no INTEGER PRIMARY KEY,
            name TEXT,
            address TEXT,
            kyc TEXT,
            mobile TEXT,
            email TEXT,
            account_type TEXT,
            balance REAL,
            interest_rate REAL,
            created_date DATETIME,
            last_updated DATETIME)''')
            
        # Drop existing transactions table if it exists    
        self.cursor.execute("DROP TABLE IF EXISTS transactions")
            
        # Transactions table with enhanced fields
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_no INTEGER,
            transaction_type TEXT,
            amount REAL,
            timestamp DATETIME,
            status TEXT,
            description TEXT,
            FOREIGN KEY (account_no) REFERENCES accounts (account_no))''')
            
        # Interest rates table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS interest_rates (
            account_type TEXT PRIMARY KEY,
            rate REAL)''')
            
        # Initialize default admin if not exists
        self.cursor.execute("SELECT COUNT(*) FROM admin")
        if self.cursor.fetchone()[0] == 0:
            default_password = hashlib.sha256("admin123".encode()).hexdigest()
            self.cursor.execute("INSERT INTO admin VALUES (?, ?)", ("admin", default_password))
            
        # Initialize interest rates if not exists
        self.cursor.execute("SELECT COUNT(*) FROM interest_rates")
        if self.cursor.fetchone()[0] == 0:
            rates = [("Savings", 4.0), ("Current", 0.0), ("Deposit", 6.5)]
            self.cursor.executemany("INSERT INTO interest_rates VALUES (?, ?)", rates)
            
        self.conn.commit()
    
    def create_account(self, name, address, kyc, mobile, email, account_type, username, password):
        try:
            # Start transaction
            self.conn.execute("BEGIN TRANSACTION")
            
            # Generate account number
            account_no = random.randint(100000, 999999)
            
            # Get interest rate
            self.cursor.execute("SELECT rate FROM interest_rates WHERE account_type=?", (account_type,))
            interest_rate = self.cursor.fetchone()[0]
            
            # Create account
            self.cursor.execute("""
                INSERT INTO accounts 
                (account_no, name, address, kyc, mobile, email, account_type, balance, interest_rate, created_date, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (account_no, name, address, kyc, mobile, email, account_type, 0, interest_rate, datetime.now(), datetime.now()))
            
            # Create user
            if not self.create_user(username, password, account_no):
                raise Exception("Username already exists")
                
            # Commit transaction
            self.conn.commit()
            return account_no
            
        except Exception as e:
            # Rollback on error
            self.conn.rollback()
            raise e
    
    def get_balance(self, account_no):
        self.cursor.execute("SELECT balance FROM accounts WHERE account_no=?", (account_no,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def update_balance(self, account_no, amount):
        self.cursor.execute("UPDATE accounts SET balance = balance + ? WHERE account_no=?", (amount, account_no))
        self.conn.commit()
    
    def record_transaction(self, account_no, transaction_type, amount):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("INSERT INTO transactions (account_no, transaction_type, amount, timestamp) VALUES (?, ?, ?, ?)",
                          (account_no, transaction_type, amount, timestamp))
        self.conn.commit()
    
    def get_transaction_history(self, account_no, start_date=None, end_date=None):
        query = """
            SELECT t.*, a.name 
            FROM transactions t 
            JOIN accounts a ON t.account_no = a.account_no 
            WHERE t.account_no = ?
        """
        params = [account_no]
        
        if start_date:
            query += " AND date(timestamp) >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date(timestamp) <= ?"
            params.append(end_date)
            
        query += " ORDER BY t.timestamp DESC"
        
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def transfer(self, from_acc, to_acc, amount):
        try:
            # Start transaction
            self.conn.execute("BEGIN TRANSACTION")
            
            # Check if accounts exist
            self.cursor.execute("SELECT balance FROM accounts WHERE account_no=?", (from_acc,))
            from_balance = self.cursor.fetchone()
            if not from_balance:
                raise Exception("Source account not found")
                
            self.cursor.execute("SELECT balance FROM accounts WHERE account_no=?", (to_acc,))
            to_balance = self.cursor.fetchone()
            if not to_balance:
                raise Exception("Destination account not found")
                
            # Check sufficient balance
            if from_balance[0] < amount:
                raise Exception("Insufficient balance")
                
            # Update balances
            self.cursor.execute("UPDATE accounts SET balance = balance - ? WHERE account_no=?", (amount, from_acc))
            self.cursor.execute("UPDATE accounts SET balance = balance + ? WHERE account_no=?", (amount, to_acc))
            
            # Record transactions
            timestamp = datetime.now()
            self.cursor.execute("""
                INSERT INTO transactions 
                (account_no, transaction_type, amount, timestamp, status, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (from_acc, "TRANSFER_OUT", -amount, timestamp, "SUCCESS", f"Transfer to {to_acc}"))
            
            self.cursor.execute("""
                INSERT INTO transactions 
                (account_no, transaction_type, amount, timestamp, status, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (to_acc, "TRANSFER_IN", amount, timestamp, "SUCCESS", f"Transfer from {from_acc}"))
            
            # Update last_updated
            self.cursor.execute("UPDATE accounts SET last_updated = ? WHERE account_no IN (?, ?)", 
                              (timestamp, from_acc, to_acc))
            
            # Commit transaction
            self.conn.commit()
            return True
            
        except Exception as e:
            # Rollback on error
            self.conn.rollback()
            raise e
    
    def close(self):
        self.conn.close()
        
    def authenticate_admin(self, username, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute("SELECT * FROM admin WHERE username=? AND password=?", 
                          (username, hashed_password))
        return self.cursor.fetchone() is not None
        
    def authenticate_user(self, username, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute("SELECT * FROM users WHERE username=? AND password=?", 
                          (username, hashed_password))
        return self.cursor.fetchone() is not None
        
    def change_password(self, username, old_password, new_password, is_admin=False):
        table = "admin" if is_admin else "users"
        hashed_old = hashlib.sha256(old_password.encode()).hexdigest()
        hashed_new = hashlib.sha256(new_password.encode()).hexdigest()
        
        self.cursor.execute(f"SELECT * FROM {table} WHERE username=? AND password=?", 
                          (username, hashed_old))
        if self.cursor.fetchone() is None:
            return False
            
        self.cursor.execute(f"UPDATE {table} SET password=? WHERE username=?", 
                          (hashed_new, username))
        self.conn.commit()
        return True
        
    def create_user(self, username, password, account_no):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        try:
            self.cursor.execute("INSERT INTO users VALUES (?, ?, ?)", 
                              (username, hashed_password, account_no))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
            
    def get_account_by_username(self, username):
        self.cursor.execute("SELECT account_no FROM users WHERE username=?", (username,))
        result = self.cursor.fetchone()
        return result[0] if result else None
        
    def get_interest_rate(self, account_type):
        self.cursor.execute("SELECT rate FROM interest_rates WHERE account_type=?", (account_type,))
        result = self.cursor.fetchone()
        return result[0] if result else 0.0
        
    def calculate_interest(self, account_no):
        self.cursor.execute("SELECT balance, account_type FROM accounts WHERE account_no=?", (account_no,))
        result = self.cursor.fetchone()
        if result:
            balance, account_type = result
            rate = self.get_interest_rate(account_type)
            return balance * (rate / 100)
        return 0.0
        
    def get_daily_transactions(self, date=None):
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute("""
            SELECT t.*, a.name 
            FROM transactions t 
            JOIN accounts a ON t.account_no = a.account_no 
            WHERE date(timestamp) = ?
            ORDER BY t.timestamp DESC
        """, (date,))
        return self.cursor.fetchall()
        
    def get_monthly_transactions(self, year, month):
        self.cursor.execute("""
            SELECT t.*, a.name 
            FROM transactions t 
            JOIN accounts a ON t.account_no = a.account_no 
            WHERE strftime('%Y', t.timestamp) = ? AND strftime('%m', t.timestamp) = ?
            ORDER BY t.timestamp DESC
        """, (year, month.zfill(2)))
        return self.cursor.fetchall()
        
    def get_yearly_transactions(self, year):
        self.cursor.execute("""
            SELECT t.*, a.name 
            FROM transactions t 
            JOIN accounts a ON t.account_no = a.account_no 
            WHERE strftime('%Y', t.timestamp) = ?
            ORDER BY t.timestamp DESC
        """, (year,))
        return self.cursor.fetchall()
        
    def get_total_accounts(self):
        self.cursor.execute("SELECT COUNT(*) FROM accounts")
        return self.cursor.fetchone()[0]
        
    def get_total_transactions(self):
        self.cursor.execute("SELECT COUNT(*) FROM transactions")
        return self.cursor.fetchone()[0]
        
    def get_total_balance(self):
        self.cursor.execute("SELECT SUM(balance) FROM accounts")
        return self.cursor.fetchone()[0] or 0.0
        
    def get_account_info(self, account_no):
        self.cursor.execute("""
            SELECT a.*, i.rate 
            FROM accounts a 
            LEFT JOIN interest_rates i ON a.account_type = i.account_type 
            WHERE a.account_no = ?
        """, (account_no,))
        result = self.cursor.fetchone()
        if result:
            return {
                'account_no': result[0],
                'name': result[1],
                'address': result[2],
                'kyc': result[3],
                'mobile': result[4],
                'email': result[5],
                'account_type': result[6],
                'balance': result[7],
                'interest_rate': result[8],
                'created_date': result[9],
                'last_updated': result[10]
            }
        return None
        
    def deposit(self, account_no, amount):
        try:
            # Start transaction
            self.conn.execute("BEGIN TRANSACTION")
            
            # Check if account exists
            self.cursor.execute("SELECT balance FROM accounts WHERE account_no=?", (account_no,))
            if not self.cursor.fetchone():
                raise Exception("Account not found")
                
            # Update balance
            self.cursor.execute("UPDATE accounts SET balance = balance + ? WHERE account_no=?", (amount, account_no))
            
            # Record transaction
            timestamp = datetime.now()
            self.cursor.execute("""
                INSERT INTO transactions 
                (account_no, transaction_type, amount, timestamp, status, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (account_no, "DEPOSIT", amount, timestamp, "SUCCESS", "Cash deposit"))
            
            # Update last_updated
            self.cursor.execute("UPDATE accounts SET last_updated = ? WHERE account_no = ?", (timestamp, account_no))
            
            # Commit transaction
            self.conn.commit()
            return True
            
        except Exception as e:
            # Rollback on error
            self.conn.rollback()
            raise e
            
    def withdraw(self, account_no, amount):
        try:
            # Start transaction
            self.conn.execute("BEGIN TRANSACTION")
            
            # Check if account exists and has sufficient balance
            self.cursor.execute("SELECT balance FROM accounts WHERE account_no=?", (account_no,))
            balance = self.cursor.fetchone()
            if not balance:
                raise Exception("Account not found")
            if balance[0] < amount:
                raise Exception("Insufficient balance")
                
            # Update balance
            self.cursor.execute("UPDATE accounts SET balance = balance - ? WHERE account_no=?", (amount, account_no))
            
            # Record transaction
            timestamp = datetime.now()
            self.cursor.execute("""
                INSERT INTO transactions 
                (account_no, transaction_type, amount, timestamp, status, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (account_no, "WITHDRAWAL", -amount, timestamp, "SUCCESS", "Cash withdrawal"))
            
            # Update last_updated
            self.cursor.execute("UPDATE accounts SET last_updated = ? WHERE account_no = ?", (timestamp, account_no))
            
            # Commit transaction
            self.conn.commit()
            return True
            
        except Exception as e:
            # Rollback on error
            self.conn.rollback()
            raise e
        
    def get_account_summary(self, account_no):
        self.cursor.execute("""
            SELECT 
                a.account_no,
                a.name,
                a.account_type,
                a.balance,
                i.rate,
                COUNT(t.id) as transaction_count,
                MAX(t.timestamp) as last_transaction
            FROM accounts a
            LEFT JOIN interest_rates i ON a.account_type = i.account_type
            LEFT JOIN transactions t ON a.account_no = t.account_no
            WHERE a.account_no = ?
            GROUP BY a.account_no
        """, (account_no,))
        return self.cursor.fetchone()

class BankApp:
    def __init__(self, root):
        self.db = BankDB()
        self.root = root
        self.root.title("Bank Management System")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")
        
        # Current user state
        self.current_user = None
        self.is_admin = False
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("TEntry", font=("Arial", 10))
        
        # Create login frame
        self.show_login_frame()
        
    def show_login_frame(self):
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Create login frame
        login_frame = ttk.Frame(self.root, padding="20")
        login_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        ttk.Label(login_frame, text="Bank Management System", font=("Arial", 20, "bold")).pack(pady=20)
        
        # Login form
        form_frame = ttk.Frame(login_frame)
        form_frame.pack(pady=20)
        
        # Username
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(form_frame, width=30)
        self.username_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Password
        ttk.Label(form_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(form_frame, width=30, show="*")
        self.password_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Login type
        self.login_type = tk.StringVar(value="user")
        ttk.Radiobutton(form_frame, text="User", variable=self.login_type, value="user").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Radiobutton(form_frame, text="Admin", variable=self.login_type, value="admin").grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Login and Signup buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Login", command=self.login).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Sign Up", command=self.show_signup).pack(side=tk.LEFT, padx=5)
        
    def show_signup(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Sign Up")
        dialog.geometry("400x500")
        
        # Form fields
        fields = [
            ("Name", "signup_name"),
            ("Address", "signup_address"),
            ("KYC ID", "signup_kyc"),
            ("Mobile", "signup_mobile"),
            ("Email", "signup_email"),
            ("Username", "signup_username"),
            ("Password", "signup_password"),
            ("Confirm Password", "signup_confirm_password")
        ]
        
        entries = {}
        for i, (label, var_name) in enumerate(fields):
            ttk.Label(dialog, text=label).pack(pady=5)
            entry = ttk.Entry(dialog, width=30)
            if "Password" in label:
                entry.configure(show="*")
            entry.pack(pady=5)
            entries[var_name] = entry
        
        # Account Type
        ttk.Label(dialog, text="Account Type").pack(pady=5)
        account_type_var = tk.StringVar()
        account_types = ["Savings", "Current", "Deposit"]
        
        radio_frame = ttk.Frame(dialog)
        radio_frame.pack(pady=5)
        
        for acc_type in account_types:
            ttk.Radiobutton(radio_frame, text=acc_type, variable=account_type_var, 
                          value=acc_type).pack(side=tk.LEFT, padx=10)
        
        def signup():
            try:
                # Validate passwords match
                if entries["signup_password"].get() != entries["signup_confirm_password"].get():
                    messagebox.showerror("Error", "Passwords do not match")
                    return
                
                # Validate all fields are filled
                if not all(entry.get() for entry in entries.values()):
                    messagebox.showerror("Error", "Please fill all fields")
                    return
                
                if not account_type_var.get():
                    messagebox.showerror("Error", "Please select an account type")
                    return
                
                # Create account
                account_no = self.db.create_account(
                    entries["signup_name"].get(),
                    entries["signup_address"].get(),
                    entries["signup_kyc"].get(),
                    entries["signup_mobile"].get(),
                    entries["signup_email"].get(),
                    account_type_var.get(),
                    entries["signup_username"].get(),
                    entries["signup_password"].get()
                )
                
                messagebox.showinfo("Success", 
                    f"Account Created Successfully!\n"
                    f"Account Number: {account_no}\n"
                    f"Username: {entries['signup_username'].get()}\n\n"
                    f"Please login with your credentials.")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(dialog, text="Create Account", command=signup).pack(pady=20)
        
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        is_admin = self.login_type.get() == "admin"
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
            
        if is_admin:
            if self.db.authenticate_admin(username, password):
                self.current_user = username
                self.is_admin = True
                self.show_main_frame()
            else:
                messagebox.showerror("Error", "Invalid admin credentials")
        else:
            if self.db.authenticate_user(username, password):
                self.current_user = username
                self.is_admin = False
                self.show_main_frame()
            else:
                messagebox.showerror("Error", "Invalid user credentials")
                
    def show_main_frame(self):
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Create main container
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with user info and logout button
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        user_info = f"Logged in as: {self.current_user} ({'Admin' if self.is_admin else 'User'})"
        ttk.Label(header_frame, text=user_info, font=("Arial", 12)).pack(side=tk.LEFT)
        ttk.Button(header_frame, text="Logout", command=self.logout).pack(side=tk.RIGHT)
        ttk.Button(header_frame, text="Change Password", command=self.show_change_password).pack(side=tk.RIGHT, padx=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs based on user type
        if self.is_admin:
            self.create_admin_tabs()
        else:
            self.create_user_tabs()
            
    def create_admin_tabs(self):
        # Admin Dashboard
        dashboard_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Statistics
        stats_frame = ttk.Frame(dashboard_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        
        total_accounts = self.db.get_total_accounts()
        total_transactions = self.db.get_total_transactions()
        total_balance = self.db.get_total_balance()
        
        ttk.Label(stats_frame, text=f"Total Accounts: {total_accounts}", font=("Arial", 12)).pack(side=tk.LEFT, padx=20)
        ttk.Label(stats_frame, text=f"Total Transactions: {total_transactions}", font=("Arial", 12)).pack(side=tk.LEFT, padx=20)
        ttk.Label(stats_frame, text=f"Total Balance: ₹{total_balance:.2f}", font=("Arial", 12)).pack(side=tk.LEFT, padx=20)
        
        # Reports
        reports_frame = ttk.Frame(dashboard_frame)
        reports_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Daily Report
        daily_frame = ttk.LabelFrame(reports_frame, text="Daily Report", padding="10")
        daily_frame.pack(fill=tk.X, pady=5)
        
        self.daily_tree = ttk.Treeview(daily_frame, columns=("Type", "Amount", "Account", "Time"), show="headings")
        self.daily_tree.heading("Type", text="Type")
        self.daily_tree.heading("Amount", text="Amount")
        self.daily_tree.heading("Account", text="Account")
        self.daily_tree.heading("Time", text="Time")
        self.daily_tree.pack(fill=tk.X)
        
        # Monthly Report
        monthly_frame = ttk.LabelFrame(reports_frame, text="Monthly Report", padding="10")
        monthly_frame.pack(fill=tk.X, pady=5)
        
        self.monthly_tree = ttk.Treeview(monthly_frame, columns=("Type", "Amount", "Account", "Date"), show="headings")
        self.monthly_tree.heading("Type", text="Type")
        self.monthly_tree.heading("Amount", text="Amount")
        self.monthly_tree.heading("Account", text="Account")
        self.monthly_tree.heading("Date", text="Date")
        self.monthly_tree.pack(fill=tk.X)
        
        # Refresh reports
        self.refresh_reports()
        
        # Add other admin tabs
        self.create_account_tab()
        self.create_transaction_tab()
        self.create_transfer_tab()
        self.create_history_tab()
        
    def create_user_tabs(self):
        # User Dashboard
        dashboard_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Account Info
        account_no = self.db.get_account_by_username(self.current_user)
        if account_no:
            account_info = self.db.get_account_info(account_no)
            if account_info:
                info_frame = ttk.LabelFrame(dashboard_frame, text="Account Information", padding="10")
                info_frame.pack(fill=tk.X, pady=10)
                
                ttk.Label(info_frame, text=f"Account Number: {account_info['account_no']}").pack(anchor=tk.W)
                ttk.Label(info_frame, text=f"Name: {account_info['name']}").pack(anchor=tk.W)
                ttk.Label(info_frame, text=f"Account Type: {account_info['account_type']}").pack(anchor=tk.W)
                ttk.Label(info_frame, text=f"Balance: ₹{account_info['balance']:.2f}").pack(anchor=tk.W)
                ttk.Label(info_frame, text=f"Interest Rate: {account_info['interest_rate']}%").pack(anchor=tk.W)
                
                # Calculate and show interest
                interest = self.db.calculate_interest(account_no)
                ttk.Label(info_frame, text=f"Monthly Interest: ₹{interest:.2f}").pack(anchor=tk.W)
        
        # Add user tabs
        self.create_transaction_tab()
        self.create_transfer_tab()
        self.create_history_tab()
        
    def refresh_reports(self):
        # Clear existing data
        for item in self.daily_tree.get_children():
            self.daily_tree.delete(item)
        for item in self.monthly_tree.get_children():
            self.monthly_tree.delete(item)
            
        # Load daily transactions
        daily_transactions = self.db.get_daily_transactions()
        for t in daily_transactions:
            self.daily_tree.insert("", "end", values=(
                t[2],  # transaction_type
                f"₹{t[3]:.2f}",  # amount
                t[6],  # name
                t[4]   # timestamp
            ))
            
        # Load monthly transactions
        current_date = datetime.now()
        monthly_transactions = self.db.get_monthly_transactions(
            str(current_date.year),
            str(current_date.month)
        )
        for t in monthly_transactions:
            self.monthly_tree.insert("", "end", values=(
                t[2],  # transaction_type
                f"₹{t[3]:.2f}",  # amount
                t[6],  # name
                t[4]   # timestamp
            ))
            
    def show_change_password(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Change Password")
        dialog.geometry("300x200")
        
        ttk.Label(dialog, text="Current Password:").pack(pady=5)
        current_password = ttk.Entry(dialog, show="*")
        current_password.pack(pady=5)
        
        ttk.Label(dialog, text="New Password:").pack(pady=5)
        new_password = ttk.Entry(dialog, show="*")
        new_password.pack(pady=5)
        
        ttk.Label(dialog, text="Confirm New Password:").pack(pady=5)
        confirm_password = ttk.Entry(dialog, show="*")
        confirm_password.pack(pady=5)
        
        def change():
            if new_password.get() != confirm_password.get():
                messagebox.showerror("Error", "New passwords do not match")
                return
                
            if self.db.change_password(
                self.current_user,
                current_password.get(),
                new_password.get(),
                self.is_admin
            ):
                messagebox.showinfo("Success", "Password changed successfully")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Current password is incorrect")
                
        ttk.Button(dialog, text="Change Password", command=change).pack(pady=10)
        
    def logout(self):
        self.current_user = None
        self.is_admin = False
        self.show_login_frame()

    def create_account_tab(self):
        account_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(account_frame, text="Create Account")
        
        # Form fields
        fields = [
            ("Name", "name_entry"),
            ("Address", "address_entry"),
            ("KYC ID", "kyc_entry"),
            ("Mobile", "mobile_entry"),
            ("Email", "email_entry"),
            ("Username", "username_entry"),
            ("Password", "password_entry")
        ]
        
        for i, (label, var_name) in enumerate(fields):
            ttk.Label(account_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            entry = ttk.Entry(account_frame, width=40)
            if label == "Password":
                entry.configure(show="*")
            entry.grid(row=i, column=1, sticky=tk.W, pady=5)
            setattr(self, var_name, entry)
        
        # Account Type
        ttk.Label(account_frame, text="Account Type").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.account_type_var = tk.StringVar()
        account_types = ["Savings", "Current", "Deposit"]
        
        # Create a frame for radio buttons to ensure proper alignment
        radio_frame = ttk.Frame(account_frame)
        radio_frame.grid(row=7, column=1, sticky=tk.W, pady=5)
        
        for i, acc_type in enumerate(account_types):
            ttk.Radiobutton(radio_frame, text=acc_type, variable=self.account_type_var, 
                          value=acc_type).pack(side=tk.LEFT, padx=10)
        
        # Create Account Button
        ttk.Button(account_frame, text="Create Account", command=self.create_account,
                  style="Accent.TButton").grid(row=8, column=0, columnspan=4, pady=20)
    
    def create_transaction_tab(self):
        transaction_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(transaction_frame, text="Transactions")
        
        # Account Number
        ttk.Label(transaction_frame, text="Account Number").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.account_entry = ttk.Entry(transaction_frame, width=30)
        self.account_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # If user is logged in, pre-fill their account number
        if not self.is_admin and self.current_user:
            account_no = self.db.get_account_by_username(self.current_user)
            if account_no:
                self.account_entry.insert(0, str(account_no))
                self.account_entry.configure(state='readonly')
        
        # Balance Check
        ttk.Button(transaction_frame, text="Check Balance", command=self.check_balance).grid(row=1, column=0, columnspan=2, pady=5)
        
        # Amount
        ttk.Label(transaction_frame, text="Amount").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.amount_entry = ttk.Entry(transaction_frame, width=30)
        self.amount_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Transaction Buttons
        ttk.Button(transaction_frame, text="Deposit", command=self.deposit).grid(row=3, column=0, pady=5)
        ttk.Button(transaction_frame, text="Withdraw", command=self.withdraw).grid(row=3, column=1, pady=5)
    
    def create_transfer_tab(self):
        transfer_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(transfer_frame, text="Transfer")
        
        # From Account
        ttk.Label(transfer_frame, text="From Account").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.from_account_entry = ttk.Entry(transfer_frame, width=30)
        self.from_account_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # If user is logged in, pre-fill their account number
        if not self.is_admin and self.current_user:
            account_no = self.db.get_account_by_username(self.current_user)
            if account_no:
                self.from_account_entry.insert(0, str(account_no))
                self.from_account_entry.configure(state='readonly')
        
        # To Account
        ttk.Label(transfer_frame, text="To Account").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.to_account_entry = ttk.Entry(transfer_frame, width=30)
        self.to_account_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Amount
        ttk.Label(transfer_frame, text="Amount").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.transfer_amount_entry = ttk.Entry(transfer_frame, width=30)
        self.transfer_amount_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Transfer Button
        ttk.Button(transfer_frame, text="Transfer", command=self.transfer).grid(row=3, column=0, columnspan=2, pady=20)
    
    def create_history_tab(self):
        history_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(history_frame, text="Transaction History")
        
        # Account Number
        ttk.Label(history_frame, text="Account Number").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.history_account_entry = ttk.Entry(history_frame, width=30)
        self.history_account_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # If user is logged in, pre-fill their account number
        if not self.is_admin and self.current_user:
            account_no = self.db.get_account_by_username(self.current_user)
            if account_no:
                self.history_account_entry.insert(0, str(account_no))
                self.history_account_entry.configure(state='readonly')
        
        # Date Range with date pickers
        date_frame = ttk.Frame(history_frame)
        date_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Default dates: last 30 days to today
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        ttk.Label(date_frame, text="From:").pack(side=tk.LEFT, padx=5)
        self.start_date_entry = DateEntry(date_frame, width=12, 
                                         year=start_date.year, month=start_date.month, day=start_date.day,
                                         background='darkblue', foreground='white', borderwidth=2)
        self.start_date_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(date_frame, text="To:").pack(side=tk.LEFT, padx=5)
        self.end_date_entry = DateEntry(date_frame, width=12,
                                       year=end_date.year, month=end_date.month, day=end_date.day,
                                       background='darkblue', foreground='white', borderwidth=2)
        self.end_date_entry.pack(side=tk.LEFT, padx=5)
        
        # View History Button
        ttk.Button(history_frame, text="View History", command=self.view_history).grid(row=2, column=0, columnspan=2, pady=5)
        
        # Create frame for matplotlib figure
        self.history_plot_frame = ttk.Frame(history_frame)
        self.history_plot_frame.grid(row=3, column=0, columnspan=2, pady=20, sticky="nsew")
        
        # Create frame for transaction table
        self.history_table_frame = ttk.Frame(history_frame)
        self.history_table_frame.grid(row=4, column=0, columnspan=2, pady=20, sticky="nsew")
        
        # Configure grid weights
        history_frame.grid_rowconfigure(3, weight=1)
        history_frame.grid_columnconfigure(0, weight=1)
    
    def create_account(self):
        try:
            name = self.name_entry.get()
            address = self.address_entry.get()
            kyc = self.kyc_entry.get()
            mobile = self.mobile_entry.get()
            email = self.email_entry.get()
            account_type = self.account_type_var.get()
            username = self.username_entry.get()
            password = self.password_entry.get()
            
            if not all([name, address, kyc, mobile, email, account_type, username, password]):
                messagebox.showerror("Error", "Please fill all fields")
                return
                
            account_no = self.db.create_account(name, address, kyc, mobile, email, account_type, username, password)
            messagebox.showinfo("Success", f"Account Created Successfully!\nAccount No: {account_no}\nUsername: {username}")
            
            # Clear entries
            for entry in [self.name_entry, self.address_entry, self.kyc_entry, 
                         self.mobile_entry, self.email_entry, self.username_entry,
                         self.password_entry]:
                entry.delete(0, tk.END)
            self.account_type_var.set("")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def check_balance(self):
        try:
            account_no = self.account_entry.get()
            if not account_no:
                messagebox.showerror("Error", "Please enter account number")
                return
                
            account_info = self.db.get_account_info(account_no)
            if account_info:
                messagebox.showinfo("Balance", 
                    f"Account Number: {account_info['account_no']}\n"
                    f"Name: {account_info['name']}\n"
                    f"Account Type: {account_info['account_type']}\n"
                    f"Balance: ₹{account_info['balance']:.2f}\n"
                    f"Interest Rate: {account_info['interest_rate']}%")
            else:
                messagebox.showerror("Error", "Account not found")
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def deposit(self):
        try:
            account_no = self.account_entry.get()
            amount = self.amount_entry.get()
            
            if not account_no or not amount:
                messagebox.showerror("Error", "Please enter account number and amount")
                return
                
            amount = float(amount)
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive")
                return
                
            self.db.deposit(account_no, amount)
            messagebox.showinfo("Success", "Amount Deposited Successfully!")
            self.amount_entry.delete(0, tk.END)
            
            # Refresh dashboard if admin
            if self.is_admin:
                self.refresh_reports()
            # Update user dashboard
            else:
                self.update_user_dashboard()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def withdraw(self):
        try:
            account_no = self.account_entry.get()
            amount = self.amount_entry.get()
            
            if not account_no or not amount:
                messagebox.showerror("Error", "Please enter account number and amount")
                return
                
            amount = float(amount)
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive")
                return
                
            self.db.withdraw(account_no, amount)
            messagebox.showinfo("Success", "Amount Withdrawn Successfully!")
            self.amount_entry.delete(0, tk.END)
            
            # Refresh dashboard if admin
            if self.is_admin:
                self.refresh_reports()
            # Update user dashboard
            else:
                self.update_user_dashboard()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def transfer(self):
        try:
            from_acc = self.from_account_entry.get()
            to_acc = self.to_account_entry.get()
            amount = self.transfer_amount_entry.get()
            
            if not all([from_acc, to_acc, amount]):
                messagebox.showerror("Error", "Please fill all fields")
                return
                
            amount = float(amount)
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive")
                return
                
            self.db.transfer(from_acc, to_acc, amount)
            messagebox.showinfo("Success", "Transfer Successful!")
            self.transfer_amount_entry.delete(0, tk.END)
            
            # Refresh dashboard if admin
            if self.is_admin:
                self.refresh_reports()
            # Update user dashboard
            else:
                self.update_user_dashboard()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def view_history(self):
        try:
            account_no = self.history_account_entry.get()
            if not account_no:
                messagebox.showerror("Error", "Please enter account number")
                return
            
            # Get date range from date pickers
            start_date = self.start_date_entry.get_date()
            end_date = self.end_date_entry.get_date()
            
            # Format dates as strings
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            # Clear previous plots and table
            for widget in self.history_plot_frame.winfo_children():
                widget.destroy()
            for widget in self.history_table_frame.winfo_children():
                widget.destroy()
            
            # Get transaction history
            transactions = self.db.get_transaction_history(account_no, start_date_str, end_date_str)
            if not transactions:
                messagebox.showinfo("Info", f"No transaction history found for account {account_no} between {start_date_str} and {end_date_str}")
                return
            
            # Create transaction table first (this should always work)
            columns = ("Type", "Amount", "Status", "Description", "Date")
            tree = ttk.Treeview(self.history_table_frame, columns=columns, show="headings")
            
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            
            # Show transactions in reverse chronological order (newest first) for the table
            for t in transactions:
                try:
                    tree.insert("", "end", values=(
                        t[2],  # transaction_type
                        f"₹{t[3]:.2f}",  # amount
                        t[5] if t[5] else "N/A",  # status
                        t[6] if t[6] else "N/A",  # description
                        t[4]   # timestamp
                    ))
                except Exception:
                    # Skip any problematic rows
                    continue
            
            # Add scrollbar to table
            scrollbar = ttk.Scrollbar(self.history_table_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Now try to create the plot
            try:
                # Get account current balance
                current_balance = self.db.get_balance(account_no) or 0
                
                # Convert timestamps to datetime objects and sort chronologically
                transaction_data = []
                for t in transactions:
                    try:
                        date = datetime.strptime(t[4], "%Y-%m-%d %H:%M:%S")
                        amount = t[3]
                        transaction_data.append((date, amount, t))
                    except ValueError:
                        # Handle possible date format issues
                        continue
                        
                # If no valid transactions, don't attempt to create plot
                if not transaction_data:
                    return
                
                # Sort by date (newest first, since transactions are in DESC order)
                transaction_data.sort(key=lambda x: x[0], reverse=True)
                
                # Calculate starting balance by working backwards
                starting_balance = current_balance
                for _, amount, _ in transaction_data:
                    starting_balance -= amount
                
                # Reverse the data for chronological display (oldest first)
                transaction_data.reverse()
                
                # Extract sorted data
                dates = [td[0] for td in transaction_data]
                amounts = [td[1] for td in transaction_data]
                
                # Calculate running balance starting from the initial balance
                running_balance = starting_balance
                balances = []
                for amount in amounts:
                    running_balance += amount
                    balances.append(running_balance)
                
                # Create plot
                fig, ax = plt.subplots(figsize=(8, 4))
                
                # Plot transaction amounts
                ax.plot(dates, amounts, marker='o', label='Transactions')
                
                # Plot running balance on a secondary axis
                ax2 = ax.twinx()
                ax2.plot(dates, balances, 'r--', label='Balance')
                
                ax.set_title("Transaction History")
                ax.set_xlabel("Date")
                ax.set_ylabel("Transaction Amount (₹)")
                ax2.set_ylabel("Balance (₹)")
                
                # Add legends
                lines1, labels1 = ax.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Embed plot in tkinter
                canvas = FigureCanvasTkAgg(fig, master=self.history_plot_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
            except Exception as e:
                print(f"Error generating plot: {e}")
                # Just show a message in the plot area if we can't create the plot
                ttk.Label(self.history_plot_frame, 
                          text="Could not generate transaction history plot. Table view is still available.").pack(pady=20)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_user_dashboard(self):
        """Update user dashboard with latest account information"""
        try:
            # Find dashboard tab
            dashboard_tab = None
            for tab_id in self.notebook.tabs():
                if self.notebook.tab(tab_id, "text") == "Dashboard":
                    dashboard_tab = self.notebook.nametowidget(tab_id)
                    break
            
            if not dashboard_tab:
                return
            
            # Clear existing widgets
            for widget in dashboard_tab.winfo_children():
                widget.destroy()
            
            # Reconstruct dashboard with latest data
            account_no = self.db.get_account_by_username(self.current_user)
            if account_no:
                account_info = self.db.get_account_info(account_no)
                if account_info:
                    info_frame = ttk.LabelFrame(dashboard_tab, text="Account Information", padding="10")
                    info_frame.pack(fill=tk.X, pady=10)
                    
                    ttk.Label(info_frame, text=f"Account Number: {account_info['account_no']}").pack(anchor=tk.W)
                    ttk.Label(info_frame, text=f"Name: {account_info['name']}").pack(anchor=tk.W)
                    ttk.Label(info_frame, text=f"Account Type: {account_info['account_type']}").pack(anchor=tk.W)
                    ttk.Label(info_frame, text=f"Balance: ₹{account_info['balance']:.2f}").pack(anchor=tk.W)
                    ttk.Label(info_frame, text=f"Interest Rate: {account_info['interest_rate']}%").pack(anchor=tk.W)
                    
                    # Calculate and show interest
                    interest = self.db.calculate_interest(account_no)
                    ttk.Label(info_frame, text=f"Monthly Interest: ₹{interest:.2f}").pack(anchor=tk.W)
                    
                    # Recent transactions section
                    recent_frame = ttk.LabelFrame(dashboard_tab, text="Recent Transactions", padding="10")
                    recent_frame.pack(fill=tk.BOTH, expand=True, pady=10)
                    
                    # Get last 5 transactions
                    transactions = self.db.get_transaction_history(account_no)[:5] 
                    
                    if transactions:
                        columns = ("Type", "Amount", "Date", "Description")
                        tree = ttk.Treeview(recent_frame, columns=columns, show="headings", height=5)
                        
                        for col in columns:
                            tree.heading(col, text=col)
                            tree.column(col, width=100)
                        
                        for t in transactions:
                            try:
                                tree.insert("", "end", values=(
                                    t[2],  # transaction_type
                                    f"₹{t[3]:.2f}",  # amount
                                    t[4],  # timestamp
                                    t[6] if t[6] else "N/A"  # description
                                ))
                            except Exception:
                                continue
                        
                        tree.pack(fill=tk.BOTH, expand=True)
                    else:
                        ttk.Label(recent_frame, text="No recent transactions").pack(pady=20)
        
        except Exception as e:
            print(f"Error updating dashboard: {e}")  # Print to console for debugging

if __name__ == "__main__":
    root = tk.Tk()
    app = BankApp(root)
    root.mainloop() 
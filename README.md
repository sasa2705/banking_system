# Banking Management System

A modern Django-based banking management system with user and admin interfaces. This application provides full banking functionality including account management, deposits, withdrawals, transfers, transaction history, and admin controls.

## Features

- **User Authentication:** Secure login and registration with password hashing
- **Account Management:** Create and manage accounts with different types (Savings, Current, Deposit)
- **Transactions:** Deposit, withdraw, and transfer money between accounts
- **Transaction History:** View detailed transaction history with filtering options
- **Dashboard:** User-specific dashboard with account summary and recent transactions
- **Admin Panel:** Admin dashboard with system-wide statistics and controls
- **Data Visualization:** Visual representation of transaction history using charts
- **Responsive Design:** Mobile-friendly interface using Bootstrap 5

## Technology Stack

- **Backend:** Python 3.x, Django 4.x
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
- **Database:** SQLite (default), easily configurable for PostgreSQL or MySQL
- **Authentication:** Django Authentication System
- **Data Visualization:** Matplotlib
- **Form Handling:** Django Crispy Forms
- **Date Handling:** Django Bootstrap Datepicker Plus

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/banking-system.git
   cd banking-system
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # For Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Create a superuser (admin):
   ```
   python manage.py createsuperuser
   ```
   
6. Initialize with demo data (optional):
   ```
   python init_data.py
   ```

7. Run the development server:
   ```
   python manage.py runserver
   ```

8. Access the application at http://127.0.0.1:8000/

## Usage

### Regular User

1. Register a new account or login with existing credentials
2. View your account details on the dashboard
3. Perform transactions (deposit, withdrawal, transfer)
4. Check transaction history
5. Update account settings

### Admin User

1. Login with admin credentials (default: username=`admin`, password=`admin123`)
2. Access the admin dashboard with system-wide statistics
3. Create and manage user accounts
4. View all transactions
5. Perform transactions on behalf of users

## Project Structure

- **banking_system/**: Main project settings and URL configurations
- **authentication/**: User authentication, registration, and related functionality
- **accounts/**: Account management, account types, balances
- **transactions/**: Transaction processing and history
- **dashboard/**: Dashboard views for users and admins
- **templates/**: HTML templates organized by app
- **static/**: CSS, JavaScript, and image files
- **media/**: User-uploaded files (if applicable)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Django Framework
- Bootstrap
- Matplotlib
 
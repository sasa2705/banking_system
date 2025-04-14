from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomAuthenticationForm, UserRegistrationForm, CustomPasswordChangeForm
from accounts.models import InterestRate

def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'authentication/login.html', {'form': form})

def register_view(request):
    """Handle user registration with account creation"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    # Check if interest rates exist, otherwise create default rates
    if InterestRate.objects.count() == 0:
        InterestRate.objects.create(account_type='Savings', rate=4.0)
        InterestRate.objects.create(account_type='Current', rate=0.0)
        InterestRate.objects.create(account_type='Deposit', rate=6.5)
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Account created successfully! Your account number is {user.account_no}")
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'authentication/register.html', {'form': form})
    
@login_required
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')
    
@login_required
def change_password_view(request):
    """Handle password change for authenticated users"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            messages.success(request, "Your password was successfully updated!")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'authentication/change_password.html', {'form': form})

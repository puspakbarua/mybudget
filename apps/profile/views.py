from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from .forms import (
    RegistrationForm,
    EmailAuthenticationForm,
    PasswordResetRequestForm,
    PasswordResetForm,
)
from .models import UserProfile
from .utils import (
    send_verification_email,
    send_password_reset_email,
    create_verification_token_for_user,
    create_password_reset_token_for_user,
)


def home(request):
    """Home page view."""
    return render(request, "home.html")


def index(request):
    """Accounts index page."""
    return render(request, "profile/index.html")


def register(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('profile_detail')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate until email verified
            user.save()
            
            # Create UserProfile and send verification email
            profile, created = UserProfile.objects.get_or_create(user=user)
            token = create_verification_token_for_user(user)
            
            try:
                send_verification_email(user, token)
                messages.success(
                    request,
                    f'Registration successful! Check your email at {user.email} to verify your account.'
                )
                return redirect('profile_verify_email_sent')
            except Exception as e:
                messages.error(request, 'Registration failed. Error sending verification email.')
                user.delete()
                return redirect('profile_register')
    else:
        form = RegistrationForm()
    
    return render(request, 'profile/register.html', {'form': form})


def verify_email_sent(request):
    """Show message after verification email is sent."""
    return render(request, 'profile/email_verification_sent.html')


def verify_email(request, token):
    """Verify user email with token."""
    try:
        profile = UserProfile.objects.get(email_verification_token=token)
    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('profile_login')
    
    # Check if token is expired
    if not profile.is_email_verification_token_valid():
        messages.error(request, 'Verification link has expired. Please register again.')
        profile.user.delete()
        return redirect('profile_register')
    
    # Mark email as verified
    profile.email_verified = True
    profile.email_verification_token = None
    profile.email_verification_token_expires_at = None
    profile.save()
    
    # Activate user
    profile.user.is_active = True
    profile.user.save()
    
    messages.success(request, 'Email verified successfully! You can now log in.')
    return redirect('profile_login')


def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('profile_detail')
    
    if request.method == 'POST':
        form = EmailAuthenticationForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Check if email is verified
            try:
                profile = user.profile
                if not profile.email_verified:
                    messages.warning(
                        request,
                        'Please verify your email before logging in. '
                        '<a href="/profile/resend-verification/">Resend verification email</a>'
                    )
                    return redirect('profile_login')
            except UserProfile.DoesNotExist:
                # Create profile if it doesn't exist
                UserProfile.objects.create(user=user, email_verified=True)
            
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('profile_detail')
    else:
        form = EmailAuthenticationForm()
    
    return render(request, 'profile/login.html', {'form': form})


def logout_view(request):
    """User logout view."""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('profile_login')
    return render(request, 'profile/logout.html')


@login_required(login_url='profile_login')
def profile(request):
    """User profile view."""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    context = {
        'profile': profile,
    }
    return render(request, 'profile/profile.html', context)


def password_reset_request(request):
    """Request password reset view."""
    if request.user.is_authenticated:
        return redirect('profile_detail')
    
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            token = create_password_reset_token_for_user(user)
            
            try:
                send_password_reset_email(user, token)
                messages.success(
                    request,
                    'Password reset instructions have been sent to your email.'
                )
                return redirect('profile_login')
            except Exception as e:
                messages.error(request, 'Error sending reset email. Please try again.')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'profile/password_reset_request.html', {'form': form})


def password_reset_confirm(request, token):
    """Password reset confirmation view."""
    try:
        profile = UserProfile.objects.get(password_reset_token=token)
        user = profile.user
    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid password reset link.')
        return redirect('profile_password_reset')
    
    # Check if token is expired
    if not profile.is_password_reset_token_valid():
        messages.error(request, 'Password reset link has expired.')
        return redirect('profile_password_reset')
    
    if request.method == 'POST':
        form = PasswordResetForm(user, request.POST)
        if form.is_valid():
            form.save()
            
            # Clear reset token
            profile.password_reset_token = None
            profile.password_reset_token_expires_at = None
            profile.save()
            
            messages.success(request, 'Password reset successfully! You can now log in.')
            return redirect('profile_login')
    else:
        form = PasswordResetForm(user)
    
    return render(request, 'profile/password_reset_confirm.html', {'form': form})


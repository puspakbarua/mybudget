from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.core.exceptions import ValidationError


class RegistrationForm(UserCreationForm):
    """Custom registration form with email field."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address',
        })
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
        })
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        })
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        """Validate email uniqueness."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Email is already registered.')
        return email

    def clean_username(self):
        """Validate username uniqueness."""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Username is already taken.')
        return username

    def save(self, commit=True):
        """Save user with email."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(forms.Form):
    """Login form accepting username or email."""
    username_or_email = forms.CharField(
        label="Username or Email",
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        })
    )

    def clean(self):
        """Validate credentials."""
        username_or_email = self.cleaned_data.get('username_or_email')
        password = self.cleaned_data.get('password')

        if username_or_email and password:
            # Try username first
            try:
                user = User.objects.get(username=username_or_email)
            except User.DoesNotExist:
                # Try email
                try:
                    user = User.objects.get(email=username_or_email)
                except User.DoesNotExist:
                    raise ValidationError('Invalid username/email or password.')

            if not user.check_password(password):
                raise ValidationError('Invalid username/email or password.')

        return self.cleaned_data

    def get_user(self):
        """Return the authenticated user object."""
        username_or_email = self.cleaned_data.get('username_or_email')
        try:
            user = User.objects.get(username=username_or_email)
        except User.DoesNotExist:
            user = User.objects.get(email=username_or_email)
        return user


class PasswordResetRequestForm(forms.Form):
    """Form to request password reset."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address',
        })
    )

    def clean_email(self):
        """Validate email exists in system."""
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise ValidationError('No account found with this email address.')
        return email

    def get_user(self):
        """Return the user object."""
        email = self.cleaned_data.get('email')
        return User.objects.get(email=email)


class PasswordResetForm(SetPasswordForm):
    """Custom password reset form."""
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New password',
        })
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
        })
    )

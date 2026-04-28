"""
Django forms for Dialogue Summarizer
"""
import re
import requests
from django import forms
from django.conf import settings


def validate_password_strength(password):
    """Enforce strong password policy."""
    if len(password) < 8:
        raise forms.ValidationError("Password must be at least 8 characters.")
    if not re.search(r'[A-Z]', password):
        raise forms.ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        raise forms.ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r'\d', password):
        raise forms.ValidationError("Password must contain at least one digit.")
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        raise forms.ValidationError("Password must contain at least one special character.")


def verify_recaptcha(recaptcha_response: str, remote_ip: str) -> bool:
    """Verify reCAPTCHA v2 response with Google."""
    try:
        data = {
            'secret': settings.RECAPTCHA_PRIVATE_KEY,
            'response': recaptcha_response,
            'remoteip': remote_ip,
        }
        r = requests.post(settings.RECAPTCHA_VERIFY_URL, data=data, timeout=5)
        result = r.json()
        return result.get('success', False)
    except Exception:
        # If reCAPTCHA verification fails (e.g., no network), skip in dev mode
        return settings.DEBUG


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Username or Email',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
        })
    )
    recaptcha = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    def clean_username(self):
        return self.cleaned_data['username'].strip()


class RegisterForm(forms.Form):
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Full Name',
        })
    )
    username = forms.CharField(
        max_length=30,
        min_length=3,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Username (3-30 chars, letters/numbers)',
            'autocomplete': 'username',
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email Address',
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password (min 8 chars)',
            'autocomplete': 'new-password',
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm Password',
            'autocomplete': 'new-password',
        })
    )
    recaptcha = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip().lower()
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise forms.ValidationError("Username can only contain letters, numbers, and underscores.")
        if username == 'admin':
            raise forms.ValidationError("This username is not allowed.")
        return username

    def clean_password(self):
        password = self.cleaned_data['password']
        validate_password_strength(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data


class UploadForm(forms.Form):
    # Accept all file types — no extension or size restriction
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'file-input',
            'accept': '*/*',
        })
    )
    description = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Optional description',
        })
    )

    def clean_file(self):
        f = self.cleaned_data['file']
        # No extension whitelist, no size cap enforced here.
        # Django automatically streams large files to a temp directory
        # when they exceed FILE_UPLOAD_MAX_MEMORY_SIZE in settings.
        return f


class ProfileForm(forms.Form):
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full Name'})
    )
    bio = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Tell us about yourself...',
            'rows': 3,
        })
    )

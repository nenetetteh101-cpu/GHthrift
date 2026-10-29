from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Address, User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "input-field",
                "placeholder": "Username or email",
                "autocomplete": "username",
                "id": "login-username",
                "aria-label": "Username or email",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "input-field",
                "placeholder": "Password",
                "autocomplete": "current-password",
                "id": "login-password",
                "aria-label": "Password",
            }
        )
    )


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        widgets = {
            "first_name": ("First name", "given-name", "signup-first-name"),
            "last_name": ("Last name", "family-name", "signup-last-name"),
            "username": ("Username", "username", "signup-username"),
            "email": ("Email address", "email", "signup-email"),
            "phone": ("Phone number (optional)", "tel", "signup-phone"),
            "password1": ("Password", "new-password", "signup-password1"),
            "password2": ("Confirm password", "new-password", "signup-password2"),
        }
        for name, (placeholder, autocomplete, field_id) in widgets.items():
            if name not in self.fields:
                continue
            self.fields[name].widget.attrs.update(
                {
                    "class": "input-field",
                    "placeholder": placeholder,
                    "autocomplete": autocomplete,
                    "id": field_id,
                    "aria-label": placeholder,
                }
            )

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ("full_name", "phone", "line1", "city", "region", "is_default")
        widgets = {
            "line1": forms.TextInput(attrs={"placeholder": "House / street / landmark"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "field-input")

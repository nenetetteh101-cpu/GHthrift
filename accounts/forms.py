from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Address, User


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone")

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

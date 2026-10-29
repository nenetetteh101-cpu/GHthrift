from django import forms

from accounts.models import Address

from .models import Order


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=120, label="Full name")
    phone = forms.CharField(max_length=20, label="Phone number")
    email = forms.EmailField(required=False, label="Email (for receipt)")
    address = forms.CharField(
        max_length=255,
        label="Delivery address",
        widget=forms.TextInput(attrs={"placeholder": "House / street / landmark"}),
    )
    city = forms.CharField(max_length=80, label="Town / city")
    region = forms.ChoiceField(choices=Address.REGION_CHOICES, label="Region")
    payment_method = forms.ChoiceField(
        choices=Order.PaymentMethod.choices, label="Payment method"
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields["full_name"].initial = user.get_full_name() or user.username
            self.fields["phone"].initial = user.phone
            self.fields["email"].initial = user.email
            default_address = user.addresses.first()
            if default_address:
                self.fields["full_name"].initial = default_address.full_name
                self.fields["phone"].initial = default_address.phone
                self.fields["address"].initial = default_address.line1
                self.fields["city"].initial = default_address.city
                self.fields["region"].initial = default_address.region

        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "field-input")

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = "".join(char for char in phone if char.isdigit())
        if len(digits) < 9:
            raise forms.ValidationError("Enter a valid Ghana phone number.")
        return phone

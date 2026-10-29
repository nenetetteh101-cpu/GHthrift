from decimal import Decimal

from django import forms
from django.db.models import Q

from .models import Dress


SORT_CHOICES = [
    ("newest", "Newest first"),
    ("price_low", "Price: low to high"),
    ("price_high", "Price: high to low"),
]


class DressFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search dresses, colours, styles...",
                "autocomplete": "off",
            }
        ),
    )
    size = forms.ChoiceField(
        required=False,
        choices=[("", "Any size")] + list(Dress.Size.choices),
    )
    occasion = forms.ChoiceField(
        required=False,
        choices=[("", "Any occasion")] + list(Dress.Occasion.choices),
    )
    color = forms.CharField(
        required=False,
        label="Colour",
        widget=forms.TextInput(attrs={"placeholder": "e.g. green"}),
    )
    min_price = forms.DecimalField(
        required=False, min_value=Decimal("0"), label="Min price (GHS)"
    )
    max_price = forms.DecimalField(
        required=False, min_value=Decimal("0"), label="Max price (GHS)"
    )
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"field-input {existing}".strip()

    def clean(self):
        cleaned = super().clean()
        min_price = cleaned.get("min_price")
        max_price = cleaned.get("max_price")
        if min_price is not None and max_price is not None and min_price > max_price:
            raise forms.ValidationError("Minimum price cannot be greater than maximum price.")
        return cleaned

    def apply(self, queryset):
        data = self.cleaned_data
        if data.get("q"):
            q = data["q"]
            queryset = queryset.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(color__icontains=q)
                | Q(style__icontains=q)
            )
        if data.get("size"):
            queryset = queryset.filter(size=data["size"])
        if data.get("occasion"):
            queryset = queryset.filter(occasion=data["occasion"])
        if data.get("color"):
            queryset = queryset.filter(color__icontains=data["color"])
        if data.get("min_price") is not None:
            queryset = queryset.filter(price__gte=data["min_price"])
        if data.get("max_price") is not None:
            queryset = queryset.filter(price__lte=data["max_price"])

        sort = data.get("sort") or "newest"
        if sort == "price_low":
            return queryset.order_by("price", "-created_at")
        if sort == "price_high":
            return queryset.order_by("-price", "-created_at")
        return queryset.order_by("-created_at")

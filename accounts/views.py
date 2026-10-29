from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import AddressForm, RegistrationForm
from .models import Address


def register(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to GHthrift, {user.first_name or user.username}!")
            return redirect("core:home")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def addresses(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if address.is_default:
                Address.objects.filter(user=request.user).update(is_default=False)
            address.save()
            messages.success(request, "Address saved.")
            return redirect("accounts:addresses")
    else:
        form = AddressForm()

    return render(
        request,
        "accounts/addresses.html",
        {"addresses": request.user.addresses.all(), "form": form},
    )

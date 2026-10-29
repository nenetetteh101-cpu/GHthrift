from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import AddressForm, LoginForm, RegistrationForm
from .models import Address


class AuthLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["login_form"] = context["form"]
        context["register_form"] = RegistrationForm()
        context["mode"] = "login"
        return context


def register(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="accounts.backends.EmailOrUsernameBackend")
            messages.success(request, f"Welcome to GHthrift, {user.first_name or user.username}!")
            return redirect("core:home")
    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
            "register_form": form,
            "login_form": LoginForm(),
            "mode": "signup",
        },
    )


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

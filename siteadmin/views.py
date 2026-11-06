from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from decimal import Decimal, InvalidOperation

from accounts.models import User
from orders.models import Order
from shop.models import Dress


def staff_required(view_func):
    decorated = user_passes_test(
        lambda u: u.is_authenticated and (u.is_staff or u.is_superuser),
        login_url="siteadmin:login",
    )(view_func)
    return decorated


def superuser_required(view_func):
    decorated = user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser,
        login_url="siteadmin:login",
    )(view_func)
    return decorated


def siteadmin_login(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect("siteadmin:dashboard")
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next") or "siteadmin:dashboard"
            return redirect(next_url)
        error = "Invalid credentials or insufficient permissions."
    return render(request, "siteadmin/login.html", {"error": error})


@staff_required
def siteadmin_logout(request):
    logout(request)
    return redirect("siteadmin:login")


@staff_required
def dashboard(request):
    total_orders = Order.objects.count()
    total_dresses = Dress.objects.count()
    total_users = User.objects.count()
    total_revenue = (
        Order.objects.filter(status="paid").aggregate(total=Sum("total_price"))["total"]
        or 0
    )
    recent_orders = (
        Order.objects.select_related("user")
        .prefetch_related("items")
        .order_by("-created_at")[:10]
    )
    low_stock = Dress.objects.filter(stock__lte=5, is_available=True).order_by("stock")[:10]
    recent_dresses = Dress.objects.order_by("-created_at")[:5]
    context = {
        "total_orders": total_orders,
        "total_dresses": total_dresses,
        "total_users": total_users,
        "total_revenue": total_revenue,
        "recent_orders": recent_orders,
        "low_stock": low_stock,
        "recent_dresses": recent_dresses,
    }
    return render(request, "siteadmin/dashboard.html", context)


@superuser_required
def users(request):
    users_qs = User.objects.all().order_by("-date_joined")
    return render(request, "siteadmin/users.html", {"users": users_qs})


@superuser_required
def user_add(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        is_staff = request.POST.get("is_staff") == "on"
        is_superuser = request.POST.get("is_superuser") == "on"
        if not username or not password:
            return render(
                request,
                "siteadmin/user_form.html",
                {"error": "Username and password are required.", "is_add": True},
            )
        if User.objects.filter(username=username).exists():
            return render(
                request,
                "siteadmin/user_form.html",
                {"error": "Username already exists.", "is_add": True},
            )
        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )
        return redirect("siteadmin:users")
    return render(request, "siteadmin/user_form.html", {"is_add": True})


@superuser_required
def user_edit(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        user.email = request.POST.get("email", "").strip()
        user.first_name = request.POST.get("first_name", "").strip()
        user.last_name = request.POST.get("last_name", "").strip()
        user.is_staff = request.POST.get("is_staff") == "on"
        user.is_superuser = request.POST.get("is_superuser") == "on"
        password = request.POST.get("password", "")
        if password:
            user.set_password(password)
        user.save()
        return redirect("siteadmin:users")
    return render(request, "siteadmin/user_form.html", {"user": user, "is_add": False})


@superuser_required
def user_delete(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user.pk == request.user.pk:
        return redirect("siteadmin:users")
    user.delete()
    return redirect("siteadmin:users")


@staff_required
def orders(request):
    status_filter = request.GET.get("status", "")
    orders_qs = (
        Order.objects.select_related("user")
        .prefetch_related("items", "payments", "delivery")
        .all()
    )
    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter)
    orders_qs = orders_qs.order_by("-created_at")
    context = {
        "orders": orders_qs,
        "status_filter": status_filter,
        "status_choices": Order.Status.choices,
    }
    return render(request, "siteadmin/orders.html", context)


@staff_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("user")
        .prefetch_related("items", "payments", "delivery"),
        pk=order_id,
    )
    if request.method == "POST":
        new_status = request.POST.get("status", "")
        if new_status in dict(Order.Status.choices):
            order.status = new_status
            if new_status == "paid" and not order.paid_at:
                order.paid_at = timezone.now()
            if new_status == "shipped" and not order.shipped_at:
                order.shipped_at = timezone.now()
            if new_status == "delivered" and not order.delivered_at:
                order.delivered_at = timezone.now()
            order.save()
        return redirect("siteadmin:order_detail", order_id=order.id)
    context = {
        "order": order,
        "status_choices": Order.Status.choices,
    }
    return render(request, "siteadmin/order_detail.html", context)


@staff_required
def dresses(request):
    dresses_qs = Dress.objects.all().order_by("-created_at")
    return render(request, "siteadmin/dresses.html", {"dresses": dresses_qs})


@staff_required
def dress_add(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        price = request.POST.get("price", "").strip()
        size = request.POST.get("size", "").strip()
        color = request.POST.get("color", "").strip()
        style = request.POST.get("style", "").strip()
        condition = request.POST.get("condition", "good")
        occasion = request.POST.get("occasion", "casual")
        stock = request.POST.get("stock", "1").strip()
        is_available = request.POST.get("is_available") == "on"
        is_featured = request.POST.get("is_featured") == "on"
        if not title or not price:
            return render(
                request,
                "siteadmin/dress_form.html",
                {
                    "error": "Title and price are required.",
                    "is_add": True,
                    "dress": {},
                    "size_choices": Dress.Size.choices,
                    "condition_choices": Dress.Condition.choices,
                    "occasion_choices": Dress.Occasion.choices,
                },
            )
        try:
            price_decimal = Decimal(price)
            stock_int = int(stock)
        except (ValueError, InvalidOperation):
            return render(
                request,
                "siteadmin/dress_form.html",
                {
                    "error": "Invalid price or stock.",
                    "is_add": True,
                    "dress": {},
                    "size_choices": Dress.Size.choices,
                    "condition_choices": Dress.Condition.choices,
                    "occasion_choices": Dress.Occasion.choices,
                },
            )
        Dress.objects.create(
            title=title,
            description=description,
            price=price_decimal,
            size=size,
            color=color,
            style=style,
            condition=condition,
            occasion=occasion,
            stock=stock_int,
            is_available=is_available,
            is_featured=is_featured,
            seller=request.user,
        )
        return redirect("siteadmin:dresses")
    context = {
        "is_add": True,
        "dress": {},
        "size_choices": Dress.Size.choices,
        "condition_choices": Dress.Condition.choices,
        "occasion_choices": Dress.Occasion.choices,
    }
    return render(request, "siteadmin/dress_form.html", context)


@staff_required
def dress_edit(request, dress_id):
    dress = get_object_or_404(Dress, pk=dress_id)
    if request.method == "POST":
        dress.title = request.POST.get("title", "").strip()
        dress.description = request.POST.get("description", "").strip()
        dress.size = request.POST.get("size", "").strip()
        dress.color = request.POST.get("color", "").strip()
        dress.style = request.POST.get("style", "").strip()
        dress.condition = request.POST.get("condition", "good")
        dress.occasion = request.POST.get("occasion", "casual")
        dress.is_available = request.POST.get("is_available") == "on"
        dress.is_featured = request.POST.get("is_featured") == "on"
        try:
            dress.price = Decimal(request.POST.get("price", "0"))
            dress.stock = int(request.POST.get("stock", "1"))
        except (ValueError, InvalidOperation):
            return render(
                request,
                "siteadmin/dress_form.html",
                {
                    "error": "Invalid price or stock.",
                    "is_add": False,
                    "dress": dress,
                    "size_choices": Dress.Size.choices,
                    "condition_choices": Dress.Condition.choices,
                    "occasion_choices": Dress.Occasion.choices,
                },
            )
        dress.save()
        return redirect("siteadmin:dresses")
    context = {
        "is_add": False,
        "dress": dress,
        "size_choices": Dress.Size.choices,
        "condition_choices": Dress.Condition.choices,
        "occasion_choices": Dress.Occasion.choices,
    }
    return render(request, "siteadmin/dress_form.html", context)


@staff_required
def dress_delete(request, dress_id):
    dress = get_object_or_404(Dress, pk=dress_id)
    dress.delete()
    return redirect("siteadmin:dresses")

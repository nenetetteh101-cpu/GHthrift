import json
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from cart.utils import get_cart

from .forms import CheckoutForm
from .models import Order, Payment
from .paystack import (
    PaystackError,
    initialize_transaction,
    is_configured,
    verify_transaction,
    verify_webhook_signature,
)
from .services import (
    create_order_from_cart,
    mark_order_paid,
    record_cod_order,
)


@login_required
def checkout(request):
    cart = get_cart(request)
    if not cart.items.exists():
        messages.info(request, "Add a dress to your cart before checking out.")
        return redirect("cart:cart_detail")

    unavailable = [
        item
        for item in cart.items.select_related("dress")
        if not item.dress.in_stock or item.quantity > item.dress.stock
    ]
    if unavailable:
        messages.error(
            request,
            "One or more dresses in your cart are no longer available. Please review your cart.",
        )
        return redirect("cart:cart_detail")

    if request.method == "POST":
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            order = create_order_from_cart(request.user, cart, form.cleaned_data)
            messages.success(request, "Order created. Complete payment to confirm it.")
            return redirect("orders:payment", reference=order.reference)
    else:
        form = CheckoutForm(user=request.user)

    delivery_fee = Decimal(str(settings.DELIVERY_FEE))
    return render(
        request,
        "orders/checkout.html",
        {
            "form": form,
            "cart": cart,
            "delivery_fee": delivery_fee,
            "total": cart.subtotal + delivery_fee,
        },
    )


@login_required
def payment(request, reference):
    order = get_object_or_404(Order, reference=reference, user=request.user)

    if order.is_paid:
        return redirect("orders:order_detail", reference=order.reference)

    if request.method == "POST":
        if order.payment_method == Order.PaymentMethod.PAY_ON_DELIVERY:
            record_cod_order(order)
            messages.success(
                request, "Order confirmed. Please have the exact amount ready on delivery."
            )
            return redirect("orders:order_detail", reference=order.reference)

        if is_configured():
            email = order.shipping_email or request.user.email
            if not email:
                messages.error(
                    request,
                    "Add an email address to your account before paying online.",
                )
                return redirect("orders:payment", reference=order.reference)
            callback_url = request.build_absolute_uri(
                reverse("orders:paystack_callback")
            )
            try:
                transaction_data = initialize_transaction(order, email, callback_url)
            except PaystackError as exc:
                messages.error(request, str(exc))
                return redirect("orders:payment", reference=order.reference)

            Payment.objects.update_or_create(
                order=order,
                provider=Payment.Provider.PAYSTACK,
                defaults={
                    "amount": order.total_price,
                    "provider_ref": order.reference,
                    "status": Payment.Status.PENDING,
                    "raw_payload": transaction_data,
                },
            )
            return redirect(transaction_data["authorization_url"])

        if settings.PAYSTACK_ALLOW_MOCK:
            mark_order_paid(
                order,
                Payment.Provider.MOCK,
                provider_ref=f"MOCK-{order.reference}",
                raw_payload={"sandbox": True},
            )
            messages.success(request, "Sandbox payment approved. Order confirmed!")
            return redirect("orders:order_detail", reference=order.reference)

        messages.error(
            request,
            "Online payments are not configured yet. Choose pay on delivery or contact us.",
        )
        return redirect("orders:payment", reference=order.reference)

    return render(
        request,
        "orders/payment.html",
        {
            "order": order,
            "paystack_configured": is_configured(),
            "allow_mock": settings.PAYSTACK_ALLOW_MOCK,
        },
    )


def paystack_callback(request):
    reference = request.GET.get("reference")
    if not reference:
        messages.error(request, "Missing payment reference.")
        return redirect("core:home")

    order = get_object_or_404(Order, reference=reference)
    try:
        data = verify_transaction(reference)
    except PaystackError as exc:
        messages.error(request, str(exc))
        return redirect("orders:order_detail", reference=order.reference)

    if data.get("status") == "success":
        try:
            amount = Decimal(str(data.get("amount", "0"))) / 100
        except InvalidOperation:
            amount = order.total_price
        if amount >= order.total_price:
            mark_order_paid(
                order,
                Payment.Provider.PAYSTACK,
                provider_ref=reference,
                raw_payload=data,
                amount=amount,
            )
            messages.success(request, "Payment received. Thank you!")
        else:
            messages.error(request, "The amount paid does not match this order.")
    else:
        messages.error(request, "Payment was not successful. Please try again.")

    return redirect("orders:order_detail", reference=order.reference)


@csrf_exempt
@require_POST
def paystack_webhook(request):
    signature = request.headers.get("X-Paystack-Signature")
    if not verify_webhook_signature(request.body, signature):
        return HttpResponse(status=401)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    if payload.get("event") == "charge.success":
        data = payload.get("data", {})
        reference = data.get("reference")
        order = Order.objects.filter(reference=reference).first()
        if order:
            try:
                amount = Decimal(str(data.get("amount", "0"))) / 100
            except InvalidOperation:
                amount = Decimal("0.00")
            if amount >= order.total_price:
                mark_order_paid(
                    order,
                    Payment.Provider.PAYSTACK,
                    provider_ref=reference,
                    raw_payload=data,
                    amount=amount,
                )

    return HttpResponse(status=200)


@login_required
def order_list(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items")
        .select_related("delivery")
    )
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def order_detail(request, reference):
    order = get_object_or_404(
        Order.objects.prefetch_related("items", "payments").select_related("delivery"),
        reference=reference,
        user=request.user,
    )
    return render(request, "orders/order_detail.html", {"order": order})

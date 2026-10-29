from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from shop.models import Dress

from .models import CartItem
from .utils import get_cart


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def cart_detail(request):
    cart = get_cart(request)
    return render(request, "cart/cart_detail.html", {"cart": cart})


@require_POST
def add_to_cart(request, pk):
    dress = get_object_or_404(Dress, pk=pk)
    cart = get_cart(request)

    if not dress.in_stock:
        messages.error(request, "Sorry, this dress is no longer available.")
        if _is_htmx(request):
            return render(
                request,
                "cart/partials/add_response.html",
                {"cart": cart, "dress": dress, "error": "This dress is sold out."},
            )
        return redirect(dress.get_absolute_url())

    item, created = CartItem.objects.get_or_create(
        cart=cart, dress=dress, defaults={"quantity": 1}
    )
    if not created and item.quantity < dress.stock:
        item.quantity += 1
        item.save(update_fields=["quantity"])

    messages.success(request, f"{dress.title} added to your cart.")

    if _is_htmx(request):
        return render(
            request,
            "cart/partials/add_response.html",
            {"cart": cart, "dress": dress},
        )
    return redirect("cart:cart_detail")


@require_POST
def update_item(request, item_id):
    cart = get_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    quantity = max(1, min(quantity, item.dress.stock))
    item.quantity = quantity
    item.save(update_fields=["quantity"])

    if _is_htmx(request):
        return render(request, "cart/partials/cart_body.html", {"cart": cart, "htmx": True})
    return redirect("cart:cart_detail")


@require_POST
def remove_item(request, item_id):
    cart = get_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()
    messages.info(request, "Item removed from your cart.")

    if _is_htmx(request):
        return render(request, "cart/partials/cart_body.html", {"cart": cart, "htmx": True})
    return redirect("cart:cart_detail")

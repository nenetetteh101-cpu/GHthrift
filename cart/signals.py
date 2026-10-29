from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import Cart, CartItem


@receiver(user_logged_in)
def merge_session_cart(sender, request, user, **kwargs):
    """Move items from an anonymous cart into the user's cart on login."""
    cart_id = request.session.get("cart_id")
    session_cart = None
    if cart_id:
        session_cart = Cart.objects.filter(pk=cart_id, user__isnull=True).first()

    if not session_cart:
        session_key = request.session.session_key
        if session_key:
            session_cart = Cart.objects.filter(
                session_key=session_key, user__isnull=True
            ).first()

    if not session_cart:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)
    for item in session_cart.items.select_related("dress"):
        if not item.dress.in_stock:
            continue
        target, created = CartItem.objects.get_or_create(
            cart=user_cart,
            dress=item.dress,
            defaults={"quantity": item.quantity},
        )
        if not created:
            target.quantity = min(target.quantity + item.quantity, item.dress.stock)
            target.save(update_fields=["quantity"])

    session_cart.delete()
    request.session.pop("cart_id", None)

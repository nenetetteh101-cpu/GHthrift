from .models import Cart


def get_cart(request, create=True):
    """Return the current cart, keyed by user or session."""
    if request.user.is_authenticated:
        if create:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            return cart
        return Cart.objects.filter(user=request.user).first()

    cart_id = request.session.get("cart_id")
    if cart_id:
        cart = Cart.objects.filter(pk=cart_id, user__isnull=True).first()
        if cart:
            return cart
        request.session.pop("cart_id", None)

    if not request.session.session_key:
        if not create:
            return None
        request.session.create()

    key = request.session.session_key
    if create:
        cart, _ = Cart.objects.get_or_create(session_key=key, user=None)
        request.session["cart_id"] = cart.pk
        return cart
    return Cart.objects.filter(session_key=key, user=None).first()

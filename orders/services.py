from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from shop.models import Dress

from .emails import send_order_receipt, send_shipped_notice
from .models import Delivery, Order, OrderItem, Payment


@transaction.atomic
def create_order_from_cart(user, cart, data):
    items = list(cart.items.select_related("dress"))
    subtotal = sum((item.line_total for item in items), start=Decimal("0.00"))
    delivery_fee = Decimal(str(settings.DELIVERY_FEE))
    total = subtotal + delivery_fee

    order = Order.objects.create(
        user=user,
        status=Order.Status.PENDING,
        payment_method=data["payment_method"],
        shipping_name=data["full_name"],
        shipping_phone=data["phone"],
        shipping_email=data.get("email") or user.email,
        shipping_address=data["address"],
        shipping_city=data["city"],
        shipping_region=data["region"],
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total_price=total,
    )

    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                dress=item.dress,
                title=item.dress.title,
                size=item.dress.size,
                unit_price=item.dress.price,
                quantity=item.quantity,
            )
            for item in items
        ]
    )

    cart.items.all().delete()
    return order


@transaction.atomic
def mark_order_paid(order, provider, provider_ref="", raw_payload=None, amount=None):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.is_paid:
        return order
    if order.status in {Order.Status.CANCELLED, Order.Status.REFUNDED}:
        return order

    order.status = Order.Status.PAID
    order.paid_at = timezone.now()
    order.transaction_id = provider_ref
    order.save(update_fields=["status", "paid_at", "transaction_id"])

    Payment.objects.update_or_create(
        order=order,
        provider=provider,
        defaults={
            "amount": amount if amount is not None else order.total_price,
            "provider_ref": provider_ref,
            "status": Payment.Status.SUCCESS,
            "captured_at": timezone.now(),
            "raw_payload": raw_payload or {},
        },
    )

    for item in order.items.select_related("dress"):
        if not item.dress_id:
            continue
        dress = Dress.objects.select_for_update().get(pk=item.dress_id)
        dress.stock = max(0, dress.stock - item.quantity)
        if dress.stock == 0:
            dress.is_available = False
        dress.save(update_fields=["stock", "is_available"])

    transaction.on_commit(lambda: send_order_receipt(order))
    return order


@transaction.atomic
def mark_order_shipped(order, partner_name="", tracking_number=""):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != Order.Status.PAID:
        return order

    order.status = Order.Status.SHIPPED
    order.shipped_at = timezone.now()
    order.save(update_fields=["status", "shipped_at"])

    delivery, _ = Delivery.objects.get_or_create(order=order)
    delivery.partner_name = partner_name or delivery.partner_name
    delivery.tracking_number = tracking_number or delivery.tracking_number
    delivery.status = Delivery.Status.IN_TRANSIT
    delivery.save()

    transaction.on_commit(lambda: send_shipped_notice(order))
    return order


@transaction.atomic
def mark_order_delivered(order):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status not in {Order.Status.PAID, Order.Status.SHIPPED}:
        return order

    now = timezone.now()
    order.status = Order.Status.DELIVERED
    order.delivered_at = now
    order.save(update_fields=["status", "delivered_at"])

    delivery, _ = Delivery.objects.get_or_create(order=order)
    delivery.status = Delivery.Status.DELIVERED
    delivery.delivered_at = now
    delivery.save()
    return order


@transaction.atomic
def record_cod_order(order):
    Payment.objects.update_or_create(
        order=order,
        provider=Payment.Provider.COD,
        defaults={
            "amount": order.total_price,
            "status": Payment.Status.PENDING,
            "raw_payload": {"note": "Cash on delivery"},
        },
    )
    return order

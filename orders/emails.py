from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone


def send_order_receipt(order):
    if not order.shipping_email:
        return
    context = {"order": order, "site_url": settings.SITE_URL}
    subject = f"Your GHthrift order {order.reference} is confirmed"
    text_body = render_to_string("orders/email/receipt.txt", context)
    html_body = render_to_string("orders/email/receipt.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.shipping_email],
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=True)


def send_shipped_notice(order):
    if not order.shipping_email:
        return
    tracking = getattr(getattr(order, "delivery", None), "tracking_number", "")
    context = {
        "order": order,
        "tracking": tracking,
        "site_url": settings.SITE_URL,
        "sent_at": timezone.now(),
    }
    message = EmailMultiAlternatives(
        subject=f"Order {order.reference} has shipped",
        body=render_to_string("orders/email/shipped.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.shipping_email],
    )
    message.send(fail_silently=True)

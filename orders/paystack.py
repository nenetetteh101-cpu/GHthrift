import hashlib
import hmac

import requests
from django.conf import settings


class PaystackError(Exception):
    pass


def is_configured():
    return bool(settings.PAYSTACK_SECRET_KEY)


def _headers():
    return {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def initialize_transaction(order, email, callback_url):
    if not is_configured():
        raise PaystackError("Paystack is not configured.")

    payload = {
        "email": email,
        "amount": int(order.total_price * 100),
        "currency": settings.PAYSTACK_CURRENCY,
        "reference": order.reference,
        "callback_url": callback_url,
        "metadata": {
            "order_id": order.pk,
            "order_reference": order.reference,
            "customer": order.shipping_name,
        },
    }
    try:
        response = requests.post(
            f"{settings.PAYSTACK_BASE_URL}/transaction/initialize",
            json=payload,
            headers=_headers(),
            timeout=20,
        )
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise PaystackError("Could not reach Paystack. Please try again.") from exc

    if not response.ok or not data.get("status"):
        raise PaystackError(data.get("message", "Paystack rejected the transaction."))

    return data["data"]


def verify_transaction(reference):
    if not is_configured():
        raise PaystackError("Paystack is not configured.")

    try:
        response = requests.get(
            f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}",
            headers=_headers(),
            timeout=20,
        )
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise PaystackError("Could not verify the payment.") from exc

    if not response.ok or not data.get("status"):
        raise PaystackError(data.get("message", "Payment verification failed."))

    return data["data"]


def verify_webhook_signature(payload_body, signature):
    if not signature or not settings.PAYSTACK_SECRET_KEY:
        return False
    expected = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
        payload_body,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

import hashlib
import hmac
import json
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from cart.models import CartItem
from shop.models import Dress

from .models import Order, Payment
from .services import mark_order_delivered, mark_order_shipped


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    PAYSTACK_ALLOW_MOCK=True,
    PAYSTACK_SECRET_KEY="",
)
class CheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ama", email="ama@example.com", password="A-strong-pass-12345"
        )
        self.dress = Dress.objects.create(
            title="Test dress",
            description="A test dress",
            price=Decimal("100.00"),
            size=Dress.Size.M,
            color="Green",
            stock=1,
        )
        self.client.force_login(self.user)
        self.client.post(reverse("cart:add", args=[self.dress.pk]))

    def checkout(self, payment_method="momo"):
        return self.client.post(
            reverse("orders:checkout"),
            {
                "full_name": "Ama Mensah",
                "phone": "0244000000",
                "email": "ama@example.com",
                "address": "12 Test Street",
                "city": "Accra",
                "region": "greater_accra",
                "payment_method": payment_method,
            },
        )

    def test_checkout_creates_order_and_clears_cart(self):
        response = self.checkout()
        order = Order.objects.get(user=self.user)
        self.assertRedirects(response, reverse("orders:payment", args=[order.reference]))
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.subtotal, Decimal("100.00"))
        self.assertEqual(order.total_price, Decimal("130.00"))
        self.assertEqual(CartItem.objects.count(), 0)

    def test_mock_payment_marks_paid_and_reduces_stock(self):
        self.checkout()
        order = Order.objects.get(user=self.user)
        response = self.client.post(reverse("orders:payment", args=[order.reference]))
        self.assertRedirects(
            response, reverse("orders:order_detail", args=[order.reference])
        )
        order.refresh_from_db()
        self.dress.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(self.dress.stock, 0)
        self.assertFalse(self.dress.is_available)
        self.assertTrue(
            Payment.objects.filter(order=order, provider=Payment.Provider.MOCK).exists()
        )

    def test_pay_on_delivery_records_cod_payment(self):
        self.checkout(payment_method="pay_on_delivery")
        order = Order.objects.get(user=self.user)
        self.client.post(reverse("orders:payment", args=[order.reference]))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertTrue(
            Payment.objects.filter(order=order, provider=Payment.Provider.COD).exists()
        )

    def test_other_user_cannot_view_order(self):
        self.checkout()
        order = Order.objects.get(user=self.user)
        other = User.objects.create_user(username="other", password="A-strong-pass-12345")
        self.client.force_login(other)
        response = self.client.get(reverse("orders:order_detail", args=[order.reference]))
        self.assertEqual(response.status_code, 404)

    def test_admin_status_helpers(self):
        self.checkout()
        order = Order.objects.get(user=self.user)
        self.client.post(reverse("orders:payment", args=[order.reference]))
        order.refresh_from_db()

        mark_order_shipped(order, partner_name="Flash Express", tracking_number="FL123")
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPED)
        self.assertEqual(order.delivery.tracking_number, "FL123")

        mark_order_delivered(order)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.DELIVERED)


@override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
class WebhookTests(TestCase):
    def test_webhook_marks_order_paid(self):
        user = User.objects.create_user(username="ama", password="A-strong-pass-12345")
        order = Order.objects.create(
            user=user,
            payment_method=Order.PaymentMethod.MOMO,
            shipping_name="Ama",
            shipping_phone="0244000000",
            shipping_address="12 Test Street",
            shipping_city="Accra",
            shipping_region="greater_accra",
            subtotal=Decimal("100.00"),
            delivery_fee=Decimal("30.00"),
            total_price=Decimal("130.00"),
        )
        payload = {
            "event": "charge.success",
            "data": {
                "reference": order.reference,
                "amount": 13000,
                "status": "success",
            },
        }
        body = json.dumps(payload).encode()
        signature = hmac.new(
            b"sk_test_secret", body, hashlib.sha512
        ).hexdigest()

        response = self.client.post(
            reverse("orders:paystack_webhook"),
            data=body,
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE=signature,
        )
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)

    def test_webhook_rejects_bad_signature(self):
        response = self.client.post(
            reverse("orders:paystack_webhook"),
            data=b"{}",
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE="wrong",
        )
        self.assertEqual(response.status_code, 401)

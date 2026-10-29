import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models

from accounts.models import Address


def generate_reference():
    return f"GH{uuid.uuid4().hex[:14].upper()}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending payment"
        PAID = "paid", "Paid"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    class PaymentMethod(models.TextChoices):
        MOMO = "momo", "Mobile Money"
        CARD = "card", "Card"
        PAY_ON_DELIVERY = "pay_on_delivery", "Pay on delivery"

    reference = models.CharField(
        max_length=32, unique=True, default=generate_reference, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)

    shipping_name = models.CharField(max_length=120)
    shipping_phone = models.CharField(max_length=20)
    shipping_email = models.EmailField(blank=True)
    shipping_address = models.CharField(max_length=255)
    shipping_city = models.CharField(max_length=80)
    shipping_region = models.CharField(max_length=30, choices=Address.REGION_CHOICES)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    transaction_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]

    def __str__(self):
        return f"Order {self.reference} - {self.get_status_display()}"

    @property
    def is_paid(self):
        return self.status in {
            self.Status.PAID,
            self.Status.SHIPPED,
            self.Status.DELIVERED,
        }

    @property
    def balance_due(self):
        return Decimal("0.00") if self.is_paid else self.total_price


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    dress = models.ForeignKey(
        "shop.Dress", on_delete=models.SET_NULL, null=True, blank=True
    )
    title = models.CharField(max_length=140)
    size = models.CharField(max_length=10, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.quantity} x {self.title}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class Payment(models.Model):
    class Provider(models.TextChoices):
        PAYSTACK = "paystack", "Paystack"
        FLUTTERWAVE = "flutterwave", "Flutterwave"
        MOCK = "mock", "Sandbox / mock"
        COD = "cod", "Cash on delivery"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    provider = models.CharField(max_length=20, choices=Provider.choices)
    provider_ref = models.CharField(max_length=120, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    captured_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_provider_display()} - {self.amount} ({self.status})"


class Delivery(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending pickup"
        IN_TRANSIT = "in_transit", "In transit"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="delivery"
    )
    partner_name = models.CharField(max_length=80, blank=True)
    tracking_number = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    notes = models.TextField(blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Delivery for {self.order.reference}"

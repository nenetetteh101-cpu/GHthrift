from django.contrib import admin

from .models import Delivery, Order, OrderItem, Payment
from .services import mark_order_delivered, mark_order_shipped


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("title", "size", "unit_price", "line_total")
    can_delete = False

    @admin.display(description="Line total")
    def line_total(self, obj):
        return obj.line_total if obj.pk else "-"


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("created_at", "captured_at")


class DeliveryInline(admin.StackedInline):
    model = Delivery
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "shipping_name",
        "status",
        "payment_method",
        "total_price",
        "created_at",
    )
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("reference", "shipping_name", "shipping_phone", "user__username")
    readonly_fields = (
        "reference",
        "subtotal",
        "delivery_fee",
        "total_price",
        "transaction_id",
        "created_at",
        "paid_at",
    )
    date_hierarchy = "created_at"
    inlines = [OrderItemInline, PaymentInline, DeliveryInline]
    actions = ["mark_shipped", "mark_delivered"]

    @admin.action(description="Mark selected orders as shipped")
    def mark_shipped(self, request, queryset):
        count = 0
        for order in queryset:
            mark_order_shipped(order)
            count += 1
        self.message_user(request, f"{count} order(s) marked as shipped.")

    @admin.action(description="Mark selected orders as delivered")
    def mark_delivered(self, request, queryset):
        count = 0
        for order in queryset:
            mark_order_delivered(order)
            count += 1
        self.message_user(request, f"{count} order(s) marked as delivered.")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "provider", "amount", "status", "created_at")
    list_filter = ("provider", "status")
    search_fields = ("order__reference", "provider_ref")


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ("order", "partner_name", "tracking_number", "status")
    list_filter = ("status", "partner_name")
    search_fields = ("order__reference", "tracking_number")

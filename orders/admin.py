from django.contrib import admin

from .models import Delivery, Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ["dress"]
    verbose_name = "Order Item"
    verbose_name_plural = "Order Items"


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "status",
        "total_price",
        "created_at",
        "shipped_at",
    )
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("order_number", "user__username", "user__email")
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"
    
    class Media:
        css = {
            "all": ("css/admin.css",)
        }


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "partner_name",
        "tracking_number",
        "status",
        "delivered_at",
    )
    list_filter = ("status", "delivered_at")
    search_fields = ("order__order_number", "tracking_number")
    
    class Media:
        css = {
            "all": ("css/admin.css",)
        }


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "provider",
        "amount",
        "status",
        "created_at",
    )
    list_filter = ("provider", "status", "created_at")
    search_fields = ("order__order_number", "provider_ref")
    readonly_fields = ("created_at", "captured_at")
    
    class Media:
        css = {
            "all": ("css/admin.css",)
        }
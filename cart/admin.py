from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.StackedInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ["dress"]
    verbose_name = "Cart Item"
    verbose_name_plural = "Cart Items"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "cart",
        "user",
        "status",
        "total_price",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("cart_id", "user__username", "user__email")
    inlines = [OrderItemInline]
    
    class Media:
        css = {
            "all": ("css/admin.css",)
        }
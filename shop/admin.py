from django.contrib import admin

from .models import Dress, DressImage, WishlistItem


class DressImageInline(admin.TabularInline):
    model = DressImage
    extra = 1


@admin.register(Dress)
class DressAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "price",
        "size",
        "occasion",
        "condition",
        "stock",
        "is_available",
        "is_featured",
        "created_at",
    )
    list_filter = ("is_available", "is_featured", "size", "occasion", "condition")
    search_fields = ("title", "description", "color", "style")
    inlines = [DressImageInline]
    actions = ["mark_featured", "unmark_featured", "mark_unavailable"]

    @admin.action(description="Feature selected dresses")
    def mark_featured(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description="Remove selected dresses from featured")
    def unmark_featured(self, request, queryset):
        queryset.update(is_featured=False)

    @admin.action(description="Mark selected dresses unavailable")
    def mark_unavailable(self, request, queryset):
        queryset.update(is_available=False)


@admin.register(DressImage)
class DressImageAdmin(admin.ModelAdmin):
    list_display = ("dress", "position", "alt_text")
    list_filter = ("dress",)


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "dress", "created_at")
    search_fields = ("user__username", "dress__title")

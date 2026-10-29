from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Address, SocialIdentity, User


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (("GHthrift", {"fields": ("phone",)}),)
    list_display = ("username", "email", "get_full_name", "phone", "is_staff", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name", "phone")
    inlines = [AddressInline]


@admin.register(SocialIdentity)
class SocialIdentityAdmin(admin.ModelAdmin):
    list_display = ("provider", "uid", "user", "created_at")
    list_filter = ("provider",)
    search_fields = ("uid", "user__username", "user__email")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "city", "region", "phone", "user", "is_default")
    list_filter = ("region", "is_default")
    search_fields = ("full_name", "city", "phone", "user__username")

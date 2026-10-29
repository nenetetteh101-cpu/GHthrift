from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("", views.order_list, name="order_list"),
    path("pay/<str:reference>/", views.payment, name="payment"),
    path("paystack/callback/", views.paystack_callback, name="paystack_callback"),
    path("paystack/webhook/", views.paystack_webhook, name="paystack_webhook"),
    path("<str:reference>/", views.order_detail, name="order_detail"),
]

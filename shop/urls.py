from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("<int:pk>/", views.dress_detail, name="dress_detail"),
    path("<int:pk>/wishlist/", views.toggle_wishlist, name="toggle_wishlist"),
]

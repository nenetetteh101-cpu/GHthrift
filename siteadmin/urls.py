from django.urls import path

from . import views

app_name = "siteadmin"

urlpatterns = [
    path("login/", views.siteadmin_login, name="login"),
    path("logout/", views.siteadmin_logout, name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("users/", views.users, name="users"),
    path("users/add/", views.user_add, name="user_add"),
    path("users/<int:user_id>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:user_id>/delete/", views.user_delete, name="user_delete"),
    path("orders/", views.orders, name="orders"),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),
    path("dresses/", views.dresses, name="dresses"),
    path("dresses/add/", views.dress_add, name="dress_add"),
    path("dresses/<int:dress_id>/edit/", views.dress_edit, name="dress_edit"),
    path("dresses/<int:dress_id>/delete/", views.dress_delete, name="dress_delete"),
]

from django.contrib.auth import views as auth_views
from django.urls import path

from . import social_auth, views

app_name = "accounts"

urlpatterns = [
    path("login/", views.AuthLoginView.as_view(), name="login"),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path("register/", views.register, name="register"),
    path(
        "social/<str:provider>/",
        social_auth.social_login,
        name="social_login",
    ),
    path(
        "social/<str:provider>/callback/",
        social_auth.social_callback,
        name="social_callback",
    ),
    path("addresses/", views.addresses, name="addresses"),
]

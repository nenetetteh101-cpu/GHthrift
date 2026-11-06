from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("site-admin/", include("siteadmin.urls")),
    path("accounts/", include("accounts.urls")),
    path("shop/", include("shop.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
    path("", include("core.urls")),
]

# Serve uploaded media when it is stored on disk. With Cloudflare R2 (or S3)
# the files are served from the bucket, so this fallback is disabled.
if not settings.USE_REMOTE_MEDIA:
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        )
    ]

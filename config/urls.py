from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

admin.site.site_header = "GHthrift Admin"
admin.site.site_title = "GHthrift"
admin.site.index_title = "Store management"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("shop/", include("shop.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
    path("", include("core.urls")),
]

# Serve uploaded media when it is stored on disk. On the VPS, nginx handles
# /media/ before this fallback; on Render the persistent disk is served here.
if not settings.USE_S3:
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        )
    ]

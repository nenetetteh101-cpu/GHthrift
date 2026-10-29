from django.http import JsonResponse
from django.shortcuts import render

from shop.models import Dress


def home(request):
    base = Dress.objects.filter(is_available=True, stock__gt=0).prefetch_related("images")
    featured = base.filter(is_featured=True)[:8]
    latest = base.order_by("-created_at")[:8]
    return render(
        request,
        "core/home.html",
        {
            "featured": featured,
            "latest": latest,
            "occasions": Dress.Occasion.choices,
        },
    )


def contact(request):
    return render(request, "core/contact.html")


def healthz(request):
    return JsonResponse({"status": "ok"})

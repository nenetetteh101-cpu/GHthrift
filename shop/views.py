from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import DressFilterForm
from .models import Dress, WishlistItem

PAGE_SIZE = 12


def _base_queryset():
    return (
        Dress.objects.filter(is_available=True, stock__gt=0)
        .prefetch_related("images")
        .select_related("seller")
    )


def product_list(request):
    form = DressFilterForm(request.GET or None)
    dresses = _base_queryset()

    if request.GET and form.is_valid():
        dresses = form.apply(dresses)

    paginator = Paginator(dresses, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)
    querystring = params.urlencode()

    context = {
        "form": form,
        "page_obj": page_obj,
        "dresses": page_obj.object_list,
        "querystring": querystring,
        "total_count": paginator.count,
    }

    if request.headers.get("HX-Request") == "true":
        return render(request, "shop/partials/product_results.html", context)
    return render(request, "shop/product_list.html", context)


def dress_detail(request, pk):
    dress = get_object_or_404(
        Dress.objects.prefetch_related("images").select_related("seller"), pk=pk
    )
    related = _base_queryset().filter(occasion=dress.occasion).exclude(pk=dress.pk)[:4]
    is_wishlisted = (
        request.user.is_authenticated
        and WishlistItem.objects.filter(user=request.user, dress=dress).exists()
    )
    return render(
        request,
        "shop/dress_detail.html",
        {"dress": dress, "related": related, "is_wishlisted": is_wishlisted},
    )


@login_required
@require_POST
def toggle_wishlist(request, pk):
    dress = get_object_or_404(Dress, pk=pk)
    item = WishlistItem.objects.filter(user=request.user, dress=dress).first()
    if item:
        item.delete()
        wishlisted = False
        messages.info(request, f"Removed {dress.title} from your wishlist.")
    else:
        WishlistItem.objects.create(user=request.user, dress=dress)
        wishlisted = True
        messages.success(request, f"Saved {dress.title} to your wishlist.")

    if request.headers.get("HX-Request") == "true":
        return render(
            request,
            "shop/partials/wishlist_button.html",
            {"dress": dress, "is_wishlisted": wishlisted},
        )
    return redirect(dress.get_absolute_url())


@login_required
def wishlist(request):
    items = (
        WishlistItem.objects.filter(user=request.user)
        .select_related("dress")
        .prefetch_related("dress__images")
    )
    return render(request, "shop/wishlist.html", {"items": items})

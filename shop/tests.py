from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Dress, WishlistItem


def make_dress(**overrides):
    data = {
        "title": "Test wrap dress",
        "description": "A test dress",
        "price": Decimal("120.00"),
        "size": Dress.Size.M,
        "color": "Green",
        "style": "Wrap",
        "condition": Dress.Condition.GOOD,
        "occasion": Dress.Occasion.WEDDING,
    }
    data.update(overrides)
    return Dress.objects.create(**data)


class ShopTests(TestCase):
    def setUp(self):
        self.dress = make_dress()
        self.other = make_dress(
            title="Blue work dress",
            size=Dress.Size.L,
            color="Blue",
            occasion=Dress.Occasion.WORK,
            price=Decimal("90.00"),
        )

    def test_home_and_list_pages(self):
        self.assertEqual(self.client.get(reverse("core:home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("shop:product_list")).status_code, 200)

    def test_filter_by_size_and_occasion(self):
        response = self.client.get(
            reverse("shop:product_list"), {"size": Dress.Size.L, "occasion": "work"}
        )
        self.assertContains(response, "Blue work dress")
        self.assertNotContains(response, "Test wrap dress")

    def test_filter_by_search_and_price(self):
        response = self.client.get(
            reverse("shop:product_list"), {"q": "blue", "max_price": "100"}
        )
        self.assertContains(response, "Blue work dress")
        self.assertNotContains(response, "Test wrap dress")

    def test_htmx_filter_returns_fragment(self):
        response = self.client.get(
            reverse("shop:product_list"),
            {"size": Dress.Size.M},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "shop/partials/product_results.html")

    def test_sold_dress_detail_still_visible(self):
        self.dress.stock = 0
        self.dress.is_available = False
        self.dress.save()
        response = self.client.get(self.dress.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sold out")

    def test_wishlist_toggle_requires_login(self):
        response = self.client.post(
            reverse("shop:toggle_wishlist", args=[self.dress.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_wishlist_toggle_adds_and_removes(self):
        user = User.objects.create_user(username="ama", password="A-strong-pass-12345")
        self.client.force_login(user)
        url = reverse("shop:toggle_wishlist", args=[self.dress.pk])

        response = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(WishlistItem.objects.filter(user=user, dress=self.dress).exists())

        self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertFalse(WishlistItem.objects.filter(user=user, dress=self.dress).exists())

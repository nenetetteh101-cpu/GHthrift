from decimal import Decimal
from types import SimpleNamespace

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from shop.models import Dress

from .models import CartItem
from .utils import get_cart


class CartTests(TestCase):
    def setUp(self):
        self.dress = Dress.objects.create(
            title="Test dress",
            description="A test dress",
            price=Decimal("100.00"),
            size=Dress.Size.M,
            color="Green",
        )

    def test_add_to_cart_anonymous(self):
        response = self.client.post(reverse("cart:add", args=[self.dress.pk]))
        self.assertRedirects(response, reverse("cart:cart_detail"))
        self.assertEqual(CartItem.objects.count(), 1)

    def test_add_to_cart_htmx_returns_toast_and_count(self):
        response = self.client.post(
            reverse("cart:add", args=[self.dress.pk]), HTTP_HX_REQUEST="true"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "added to your cart")
        self.assertContains(response, 'hx-swap-oob="true"')

    def test_cart_merges_on_login(self):
        self.client.post(reverse("cart:add", args=[self.dress.pk]))
        user = User.objects.create_user(username="ama", password="A-strong-pass-12345")
        self.client.post(
            reverse("accounts:login"),
            {"username": "ama", "password": "A-strong-pass-12345"},
        )
        request = SimpleNamespace(user=user, session=self.client.session)
        self.assertEqual(get_cart(request).items.count(), 1)

    def test_update_quantity_and_remove(self):
        self.dress.stock = 5
        self.dress.save(update_fields=["stock"])
        self.client.post(reverse("cart:add", args=[self.dress.pk]))
        item = CartItem.objects.get()
        self.client.post(
            reverse("cart:update", args=[item.pk]),
            {"quantity": 3},
            HTTP_HX_REQUEST="true",
        )
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)

        self.client.post(
            reverse("cart:remove", args=[item.pk]), HTTP_HX_REQUEST="true"
        )
        self.assertEqual(CartItem.objects.count(), 0)

    def test_cannot_exceed_stock(self):
        self.client.post(reverse("cart:add", args=[self.dress.pk]))
        item = CartItem.objects.get()
        self.client.post(reverse("cart:update", args=[item.pk]), {"quantity": 99})
        item.refresh_from_db()
        self.assertEqual(item.quantity, self.dress.stock)

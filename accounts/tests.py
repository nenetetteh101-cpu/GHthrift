from django.test import TestCase
from django.urls import reverse

from .models import User


class AccountViewsTests(TestCase):
    def test_register_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "ama",
                "first_name": "Ama",
                "last_name": "Mensah",
                "email": "ama@example.com",
                "phone": "0244000000",
                "password1": "A-strong-pass-12345",
                "password2": "A-strong-pass-12345",
            },
        )
        self.assertRedirects(response, reverse("core:home"))
        self.assertTrue(User.objects.filter(username="ama").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(
            username="first", email="same@example.com", password="A-strong-pass-12345"
        )
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "second",
                "email": "same@example.com",
                "password1": "A-strong-pass-12345",
                "password2": "A-strong-pass-12345",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")

    def test_login_and_logout(self):
        User.objects.create_user(
            username="kofi", password="A-strong-pass-12345"
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "kofi", "password": "A-strong-pass-12345"},
        )
        self.assertRedirects(response, reverse("core:home"))
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("core:home"))

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.get_full_name() or self.username


class SocialIdentity(models.Model):
    PROVIDER_CHOICES = [
        ("google", "Google"),
        ("instagram", "Instagram"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="social_identities"
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    uid = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["provider"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "uid"], name="unique_social_identity"
            )
        ]

    def __str__(self):
        return f"{self.get_provider_display()} · {self.user}"


class SocialProviderSettings(models.Model):
    provider = models.CharField(
        max_length=20, choices=SocialIdentity.PROVIDER_CHOICES, unique=True
    )
    client_id = models.CharField(max_length=255, blank=True)
    client_secret = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["provider"]
        verbose_name = "social provider settings"
        verbose_name_plural = "social provider settings"

    def __str__(self):
        return self.get_provider_display()


class Address(models.Model):
    REGION_CHOICES = [
        ("greater_accra", "Greater Accra"),
        ("ashanti", "Ashanti"),
        ("western", "Western"),
        ("central", "Central"),
        ("eastern", "Eastern"),
        ("volta", "Volta"),
        ("northern", "Northern"),
        ("upper_east", "Upper East"),
        ("upper_west", "Upper West"),
        ("savannah", "Savannah"),
        ("bono", "Bono"),
        ("bono_east", "Bono East"),
        ("ahafo", "Ahafo"),
        ("oti", "Oti"),
        ("north_east", "North East"),
        ("western_north", "Western North"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    line1 = models.CharField("address", max_length=255)
    city = models.CharField(max_length=80)
    region = models.CharField(max_length=30, choices=REGION_CHOICES)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.full_name}, {self.city}"

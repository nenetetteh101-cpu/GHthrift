from django.conf import settings
from django.db import models
from django.urls import reverse


class Dress(models.Model):
    class Size(models.TextChoices):
        XS = "XS", "XS"
        S = "S", "S"
        M = "M", "M"
        L = "L", "L"
        XL = "XL", "XL"
        XXL = "XXL", "XXL"
        CUSTOM = "CUSTOM", "Custom"

    class Condition(models.TextChoices):
        NEW = "new", "New with tags"
        LIKE_NEW = "like_new", "Like new"
        GOOD = "good", "Good"
        FAIR = "fair", "Fair"

    class Occasion(models.TextChoices):
        CASUAL = "casual", "Casual"
        WORK = "work", "Work"
        PARTY = "party", "Party"
        WEDDING = "wedding", "Wedding"
        CHURCH = "church", "Church"
        EVENING = "evening", "Evening"

    title = models.CharField(max_length=140)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=10, choices=Size.choices)
    color = models.CharField(max_length=40)
    style = models.CharField(max_length=80, blank=True, help_text="e.g. wrap, midi, bodycon")
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.GOOD)
    occasion = models.CharField(max_length=20, choices=Occasion.choices, default=Occasion.CASUAL)
    stock = models.PositiveIntegerField(default=1)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="listed_dresses",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_available", "stock"]),
            models.Index(fields=["size"]),
            models.Index(fields=["occasion"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("shop:dress_detail", args=[self.pk])

    @property
    def in_stock(self):
        return self.is_available and self.stock > 0

    @property
    def primary_image(self):
        images = list(self.images.all())
        return images[0] if images else None

    def save(self, *args, **kwargs):
        if self.stock <= 0:
            self.is_available = False
        super().save(*args, **kwargs)


class DressImage(models.Model):
    dress = models.ForeignKey(Dress, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="dresses/%Y/%m/")
    alt_text = models.CharField(max_length=160, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"Image for {self.dress.title}"


class WishlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist"
    )
    dress = models.ForeignKey(Dress, on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "dress")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.dress}"

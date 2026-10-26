from django.conf import settings
from django.db import models


class Profile(models.Model):
    VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("followers", "Followers only"),
        ("private", "Private"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.CharField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to="profile_pics/", blank=True)
    cover_photo = models.ImageField(upload_to="cover_photos/", blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    visibility = models.CharField(
        max_length=10, choices=VISIBILITY_CHOICES, default="public"
    )
    joined_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} profile"

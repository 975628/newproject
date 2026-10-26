from django.conf import settings
from django.db import models


class Notification(models.Model):
    KIND_CHOICES = [
        ("like", "Like"),
        ("comment", "Comment"),
        ("follow", "Follow"),
        ("friend_request", "Friend request"),
        ("friend_accepted", "Friend request accepted"),
    ]
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications_sent",
    )
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    message = models.CharField(max_length=255)
    post = models.ForeignKey(
        "posts.Post", on_delete=models.CASCADE, null=True, blank=True
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read", "-created_at"])]

    def __str__(self):
        return f"{self.message} → {self.recipient}"

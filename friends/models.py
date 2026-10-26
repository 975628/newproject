from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Follow(models.Model):
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following"
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_user", "to_user"], name="unique_user_follow"
            ),
            models.CheckConstraint(
                condition=~Q(from_user=models.F("to_user")), name="no_self_follow"
            ),
        ]

    def clean(self):
        if self.from_user_id == self.to_user_id:
            raise ValidationError("You cannot follow yourself.")

    def __str__(self):
        return f"{self.from_user} follows {self.to_user}"


class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
    ]
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_friend_requests"
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_friend_requests",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["sender", "receiver"], name="unique_friend_request_direction"
            ),
            models.CheckConstraint(
                condition=~Q(sender=models.F("receiver")), name="no_self_friend_request"
            ),
        ]

    def clean(self):
        if self.sender_id == self.receiver_id:
            raise ValidationError("You cannot send a friend request to yourself.")

    def __str__(self):
        return f"{self.sender} → {self.receiver} ({self.status})"


class Block(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_users"
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["blocker", "blocked"], name="unique_user_block"),
            models.CheckConstraint(
                condition=~Q(blocker=models.F("blocked")), name="no_self_block"
            ),
        ]

    def __str__(self):
        return f"{self.blocker} blocks {self.blocked}"

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Post(models.Model):
    AUDIENCE_CHOICES = [
        ("public", "Public"),
        ("followers", "Followers"),
        ("friends", "Friends"),
        ("private", "Only me"),
    ]

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    content = models.TextField(max_length=5000, blank=True)
    image = models.ImageField(upload_to="post_images/", blank=True)
    audience = models.CharField(
        max_length=10, choices=AUDIENCE_CHOICES, default="public"
    )
    comments_enabled = models.BooleanField(default=True)
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="Like", related_name="liked_posts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at", "audience"])]

    def clean(self):
        if not self.content.strip() and not self.image:
            raise ValidationError("A post must include text or an image.")

    def __str__(self):
        return f"Post by {self.author.username} at {self.created_at:%Y-%m-%d %H:%M}"


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="like_set")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_likes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["post", "user"], name="unique_post_like")
        ]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.username} on post {self.post_id}"


class Report(models.Model):
    STATUS_CHOICES = [("open", "Open"), ("reviewed", "Reviewed"), ("dismissed", "Dismissed")]
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, null=True, blank=True, related_name="reports"
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reports",
    )
    reason = models.CharField(max_length=500)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if (self.post is None) == (self.comment is None):
            raise ValidationError("A report must target exactly one post or comment.")

    def __str__(self):
        return f"Report #{self.pk} ({self.status})"

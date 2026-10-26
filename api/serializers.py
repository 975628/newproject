from rest_framework import serializers

from django.contrib.auth import get_user_model
from friends.models import Follow, FriendRequest
from notifications.models import Notification
from posts.models import Comment, Post
from users.models import Profile

User = get_user_model()


class PostSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username", read_only=True)
    like_count = serializers.IntegerField(source="likes.count", read_only=True)
    comment_count = serializers.IntegerField(source="comments.count", read_only=True)
    liked_by_user = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "content",
            "image",
            "audience",
            "comments_enabled",
            "like_count",
            "comment_count",
            "liked_by_user",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "author", "created_at", "updated_at")

    def validate(self, attrs):
        content = attrs.get(
            "content", self.instance.content if self.instance is not None else ""
        )
        image = attrs.get(
            "image", self.instance.image if self.instance is not None else None
        )
        if not content.strip() and not image:
            raise serializers.ValidationError(
                "A post must include text or an image."
            )
        return attrs

    def get_liked_by_user(self, post):
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_authenticated
            and post.likes.filter(pk=request.user.pk).exists()
        )


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username", read_only=True)
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())

    class Meta:
        model = Comment
        fields = ("id", "post", "author", "content", "created_at")
        read_only_fields = ("id", "author", "created_at")


class FollowSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="to_user.username", read_only=True)

    class Meta:
        model = Follow
        fields = ("id", "username", "created_at")
        read_only_fields = fields


class FriendRequestSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source="sender.username", read_only=True)
    receiver = serializers.CharField(source="receiver.username", read_only=True)
    receiver_id = serializers.PrimaryKeyRelatedField(
        source="receiver", queryset=User.objects.all(), write_only=True
    )

    class Meta:
        model = FriendRequest
        fields = ("id", "sender", "receiver", "receiver_id", "status", "created_at")
        read_only_fields = ("id", "sender", "receiver", "status", "created_at")


class NotificationSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = Notification
        fields = ("id", "actor", "kind", "message", "post", "is_read", "created_at")
        read_only_fields = ("id", "actor", "kind", "message", "post", "created_at")


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    follower_count = serializers.IntegerField(
        source="user.followers.count", read_only=True
    )
    following_count = serializers.IntegerField(
        source="user.following.count", read_only=True
    )

    class Meta:
        model = Profile
        fields = (
            "username",
            "bio",
            "profile_picture",
            "cover_photo",
            "location",
            "website",
            "visibility",
            "follower_count",
            "following_count",
            "joined_date",
        )
        read_only_fields = fields

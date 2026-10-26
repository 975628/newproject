from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from friends.models import Follow, FriendRequest
from notifications.models import Notification
from notifications.services import create_notification
from posts.models import Comment, Post
from users.access import can_view_post, is_blocked_between, visible_posts_for
from users.models import Profile
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    CommentSerializer,
    FollowSerializer,
    FriendRequestSerializer,
    NotificationSerializer,
    PostSerializer,
    ProfileSerializer,
)

User = get_user_model()


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        return visible_posts_for(self.request.user).select_related(
            "author", "author__profile"
        ).prefetch_related("likes", "comments")

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Sign in to create posts.")
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        like, created = post.like_set.get_or_create(user=request.user)
        if created:
            create_notification(
                recipient=post.author,
                actor=request.user,
                kind="like",
                message=f"{request.user.username} liked your post.",
                post=post,
            )
        else:
            like.delete()
        return Response(
            {"liked": created, "like_count": post.likes.count()},
            status=status.HTTP_200_OK,
        )


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(
            post__in=visible_posts_for(self.request.user)
        ).select_related("author", "post")

    def perform_create(self, serializer):
        post = serializer.validated_data["post"]
        if not can_view_post(self.request.user, post) or not post.comments_enabled:
            raise PermissionDenied("Comments are unavailable for this post.")
        comment = serializer.save(author=self.request.user)
        create_notification(
            recipient=post.author,
            actor=self.request.user,
            kind="comment",
            message=f"{self.request.user.username} commented on your post.",
            post=post,
        )


class FollowViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Follow.objects.filter(from_user=self.request.user).select_related("to_user")

    def create(self, request, *args, **kwargs):
        target = get_object_or_404(User, pk=request.data.get("user_id"))
        if target == request.user or is_blocked_between(request.user, target):
            raise PermissionDenied("You cannot follow this account.")
        follow, created = Follow.objects.get_or_create(
            from_user=request.user, to_user=target
        )
        if created:
            create_notification(
                recipient=target,
                actor=request.user,
                kind="follow",
                message=f"{request.user.username} started following you.",
            )
        serializer = self.get_serializer(follow)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class FriendRequestViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    serializer_class = FriendRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FriendRequest.objects.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        ).select_related("sender", "receiver")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target = serializer.validated_data["receiver"]
        if target == request.user or is_blocked_between(request.user, target):
            raise PermissionDenied("You cannot send this friend request.")

        accepted = FriendRequest.objects.filter(status="accepted").filter(
            Q(sender=request.user, receiver=target)
            | Q(sender=target, receiver=request.user)
        ).first()
        if accepted:
            return Response(self.get_serializer(accepted).data, status=status.HTTP_200_OK)

        reverse_request = FriendRequest.objects.filter(
            sender=target, receiver=request.user, status="pending"
        ).first()
        if reverse_request:
            reverse_request.status = "accepted"
            reverse_request.save(update_fields=["status", "updated_at"])
            create_notification(
                recipient=target,
                actor=request.user,
                kind="friend_accepted",
                message=f"{request.user.username} accepted your friend request.",
            )
            result = self.get_serializer(reverse_request)
            return Response(result.data, status=status.HTTP_200_OK)

        friend_request, created = FriendRequest.objects.get_or_create(
            sender=request.user, receiver=target, defaults={"status": "pending"}
        )
        if not created and friend_request.status != "pending":
            friend_request.status = "pending"
            friend_request.save(update_fields=["status", "updated_at"])
            created = True
        if created:
            create_notification(
                recipient=target,
                actor=request.user,
                kind="friend_request",
                message=f"{request.user.username} sent you a friend request.",
            )
        result = self.get_serializer(friend_request)
        return Response(
            result.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def respond(self, request, pk=None):
        friend_request = self.get_object()
        if friend_request.receiver_id != request.user.pk:
            raise PermissionDenied("Only the recipient can respond to this request.")
        if is_blocked_between(friend_request.sender, friend_request.receiver):
            raise PermissionDenied("This request is unavailable.")
        if friend_request.status != "pending":
            return Response(
                {"detail": "This request is no longer pending."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        action_name = request.data.get("action")
        if action_name not in {"accept", "decline"}:
            return Response(
                {"detail": "Action must be 'accept' or 'decline'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        friend_request.status = (
            "accepted" if action_name == "accept" else "declined"
        )
        friend_request.save(update_fields=["status", "updated_at"])
        if action_name == "accept":
            create_notification(
                recipient=friend_request.sender,
                actor=request.user,
                kind="friend_accepted",
                message=f"{request.user.username} accepted your friend request.",
            )
        return Response(self.get_serializer(friend_request).data)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related(
            "actor"
        )

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response({"is_read": True})


class ProfileDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, username):
        person = get_object_or_404(User.objects.select_related("profile"), username=username)
        from users.access import can_view_profile

        if not can_view_profile(request.user, person):
            raise PermissionDenied("This profile is private or unavailable.")
        return Response(ProfileSerializer(person.profile, context={"request": request}).data)

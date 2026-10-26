from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from notifications.services import create_notification
from users.access import is_blocked_between
from .models import Block, Follow, FriendRequest

User = get_user_model()


@login_required
@require_GET
def friend_center(request):
    incoming = request.user.received_friend_requests.filter(
        status="pending"
    ).select_related("sender")
    outgoing = request.user.sent_friend_requests.filter(
        status="pending"
    ).select_related("receiver")
    accepted = FriendRequest.objects.filter(status="accepted").filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related("sender", "receiver")
    return render(
        request,
        "friends.html",
        {"incoming": incoming, "outgoing": outgoing, "accepted": accepted},
    )


@login_required
@require_POST
def follow_user(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target == request.user or is_blocked_between(request.user, target):
        messages.error(request, "You cannot follow this account.")
        return redirect("home")
    follow, created = Follow.objects.get_or_create(from_user=request.user, to_user=target)
    if created:
        create_notification(
            recipient=target,
            actor=request.user,
            kind="follow",
            message=f"{request.user.username} started following you.",
        )
        messages.success(request, f"You are now following {target.username}.")
    else:
        follow.delete()
        messages.info(request, f"You unfollowed {target.username}.")
    return redirect("profile", username=target.username)


@login_required
@require_POST
def send_friend_request(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target == request.user or is_blocked_between(request.user, target):
        messages.error(request, "You cannot send this friend request.")
        return redirect("home")
    if FriendRequest.objects.filter(status="accepted").filter(
        Q(sender=request.user, receiver=target)
        | Q(sender=target, receiver=request.user)
    ).exists():
        messages.info(request, f"You and {target.username} are already friends.")
        return redirect("profile", username=target.username)
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
        messages.success(request, f"You and {target.username} are now friends.")
        return redirect("profile", username=target.username)
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
        messages.success(request, "Friend request sent.")
    else:
        messages.info(request, "A friend request is already pending.")
    return redirect("profile", username=target.username)


@login_required
@require_POST
def respond_friend_request(request, request_id):
    friend_request = get_object_or_404(
        FriendRequest, pk=request_id, receiver=request.user, status="pending"
    )
    if is_blocked_between(friend_request.sender, friend_request.receiver):
        messages.error(request, "This request is unavailable.")
        return redirect("friends")
    action = request.POST.get("action")
    if action == "accept":
        friend_request.status = "accepted"
        friend_request.save(update_fields=["status", "updated_at"])
        create_notification(
            recipient=friend_request.sender,
            actor=request.user,
            kind="friend_accepted",
            message=f"{request.user.username} accepted your friend request.",
        )
        messages.success(request, "Friend request accepted.")
    elif action == "decline":
        friend_request.status = "declined"
        friend_request.save(update_fields=["status", "updated_at"])
        messages.info(request, "Friend request declined.")
    else:
        messages.error(request, "Unknown friend-request action.")
    return redirect("friends")


@login_required
@require_POST
def block_user(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target == request.user:
        messages.error(request, "You cannot block yourself.")
        return redirect("home")
    Block.objects.get_or_create(blocker=request.user, blocked=target)
    Follow.objects.filter(
        Q(from_user=request.user, to_user=target)
        | Q(from_user=target, to_user=request.user)
    ).delete()
    messages.success(request, f"{target.username} has been blocked.")
    return redirect("home")


@login_required
@require_POST
def unblock_user(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    Block.objects.filter(blocker=request.user, blocked=target).delete()
    messages.success(request, f"{target.username} has been unblocked.")
    return redirect("profile", username=target.username)

from django.db.models import Q

from friends.models import Block, Follow, FriendRequest
from posts.models import Post


def is_blocked_between(user, other):
    if not user.is_authenticated:
        return False
    return Block.objects.filter(
        Q(blocker=user, blocked=other) | Q(blocker=other, blocked=user)
    ).exists()


def can_view_profile(viewer, owner):
    if viewer.is_authenticated and viewer.pk == owner.pk:
        return True
    if is_blocked_between(viewer, owner):
        return False
    visibility = getattr(getattr(owner, "profile", None), "visibility", "public")
    if visibility == "public":
        return True
    return (
        viewer.is_authenticated
        and visibility == "followers"
        and Follow.objects.filter(from_user=viewer, to_user=owner).exists()
    )


def are_friends(user, other):
    if not user.is_authenticated:
        return False
    return FriendRequest.objects.filter(
        status="accepted"
    ).filter(
        Q(sender=user, receiver=other) | Q(sender=other, receiver=user)
    ).exists()


def can_view_post(viewer, post):
    if not can_view_profile(viewer, post.author):
        return False
    if viewer.is_authenticated and viewer.pk == post.author_id:
        return True
    if post.audience == "public":
        return True
    if not viewer.is_authenticated:
        return False
    if post.audience == "followers":
        return Follow.objects.filter(from_user=viewer, to_user=post.author).exists()
    if post.audience == "friends":
        return are_friends(viewer, post.author)
    return False


def visible_posts_for(user):
    if not user.is_authenticated:
        return Post.objects.filter(
            audience="public", author__profile__visibility="public"
        )
    followed_ids = Follow.objects.filter(from_user=user).values_list(
        "to_user_id", flat=True
    )
    friend_requests = FriendRequest.objects.filter(status="accepted").filter(
        Q(sender=user) | Q(receiver=user)
    )
    friend_ids = friend_requests.values_list("sender_id", "receiver_id")
    friends = set()
    for sender_id, receiver_id in friend_ids:
        friends.add(receiver_id if sender_id == user.pk else sender_id)
    allowed = Q(author=user) | Q(
        audience="public", author__profile__visibility="public"
    )
    allowed |= Q(
        author_id__in=followed_ids,
        audience__in=["public", "followers"],
        author__profile__visibility__in=["public", "followers"],
    )
    if friends:
        allowed |= Q(
            author_id__in=friends,
            audience__in=["public", "followers", "friends"],
            author__profile__visibility__in=["public", "followers"],
        )
    blocked_ids = Block.objects.filter(blocker=user).values_list(
        "blocked_id", flat=True
    )
    blocker_ids = Block.objects.filter(blocked=user).values_list(
        "blocker_id", flat=True
    )
    return Post.objects.filter(allowed).exclude(
        Q(author_id__in=blocked_ids) | Q(author_id__in=blocker_ids)
    ).distinct()

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from friends.models import Block, Follow
from posts.forms import PostForm
from .access import can_view_profile, visible_posts_for
from .forms import ProfileForm, RegistrationForm


User = get_user_model()


def home(request):
    form = PostForm()
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("login")
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Your post has been shared.")
            return redirect("home")

    posts = visible_posts_for(request.user).select_related(
        "author", "author__profile"
    ).prefetch_related("likes", "comments__author")
    query = request.GET.get("q", "").strip()
    if query:
        posts = posts.filter(
            Q(content__icontains=query) | Q(author__username__icontains=query)
        )
    suggested_users = User.objects.none()
    people_results = User.objects.none()
    if request.user.is_authenticated:
        following_ids = Follow.objects.filter(from_user=request.user).values_list(
            "to_user_id", flat=True
        )
        blocked_ids = Block.objects.filter(
            Q(blocker=request.user) | Q(blocked=request.user)
        ).values_list("blocker_id", "blocked_id")
        hidden_ids = set()
        for blocker_id, blocked_id in blocked_ids:
            hidden_ids.add(blocked_id if blocker_id == request.user.pk else blocker_id)
        suggested_users = User.objects.exclude(
            Q(pk=request.user.pk) | Q(pk__in=following_ids) | Q(pk__in=hidden_ids)
        ).filter(profile__visibility="public")[:5]
    if query:
        people_results = User.objects.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query),
            profile__visibility="public",
        ).select_related("profile")
        if request.user.is_authenticated:
            people_results = people_results.exclude(
                Q(pk=request.user.pk) | Q(pk__in=hidden_ids)
            )
        people_results = people_results[:10]
    return render(
        request,
        "home.html",
        {
            "form": form,
            "posts": posts[:50],
            "query": query,
            "people_results": people_results,
            "suggested_users": suggested_users,
        },
    )


def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome to ConnectSphere!")
        return redirect("home")
    return render(request, "register.html", {"form": form})


@require_http_methods(["GET", "POST"])
@login_required
def edit_profile(request):
    profile = request.user.profile
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile was updated.")
        return redirect("profile", username=request.user.username)
    return render(request, "edit_profile.html", {"form": form})


def profile(request, username):
    person = get_object_or_404(User.objects.select_related("profile"), username=username)
    if not can_view_profile(request.user, person):
        messages.error(request, "This profile is private or unavailable.")
        return redirect("home")
    posts = visible_posts_for(request.user).filter(author=person).select_related(
        "author", "author__profile"
    ).prefetch_related("likes", "comments__author")
    is_following = request.user.is_authenticated and Follow.objects.filter(
        from_user=request.user, to_user=person
    ).exists()
    return render(
        request,
        "profile.html",
        {
            "profile_user": person,
            "posts": posts,
            "is_following": is_following,
        },
    )

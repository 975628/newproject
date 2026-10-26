from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from notifications.services import create_notification
from users.access import can_view_post
from .forms import CommentForm, ReportForm
from .models import Comment, Like, Post, Report


def _redirect_after_action(request):
    next_url = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect("home")


@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(Post.objects.select_related("author"), pk=post_id)
    if not can_view_post(request.user, post):
        messages.error(request, "You cannot interact with this post.")
        return redirect("home")
    like, created = Like.objects.get_or_create(post=post, user=request.user)
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
    return _redirect_after_action(request)


@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post.objects.select_related("author"), pk=post_id)
    if not can_view_post(request.user, post) or not post.comments_enabled:
        messages.error(request, "Comments are unavailable for this post.")
        return redirect("home")
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        create_notification(
            recipient=post.author,
            actor=request.user,
            kind="comment",
            message=f"{request.user.username} commented on your post.",
            post=post,
        )
    else:
        messages.error(request, "Please enter a comment.")
    return _redirect_after_action(request)


@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id, author=request.user)
    post.delete()
    messages.success(request, "Your post was deleted.")
    return redirect("home")


@login_required
@require_POST
def report_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not can_view_post(request.user, post):
        messages.error(request, "You cannot report this post.")
        return redirect("home")
    form = ReportForm(request.POST)
    if form.is_valid():
        Report.objects.create(
            reporter=request.user, post=post, reason=form.cleaned_data["reason"]
        )
        messages.success(request, "Thanks. Your report was sent to moderators.")
    else:
        messages.error(request, "Please provide a reason for the report.")
    return _redirect_after_action(request)

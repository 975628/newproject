from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def inbox(request):
    notifications = request.user.notifications.select_related("actor", "post")[:100]
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, "notifications.html", {"notifications": notifications})


@login_required
@require_POST
def mark_read(request, notification_id):
    notification = get_object_or_404(
        Notification, pk=notification_id, recipient=request.user
    )
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return redirect("notifications")

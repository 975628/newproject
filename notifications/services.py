from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Notification


def create_notification(*, recipient, actor, kind, message, post=None):
    if recipient.pk == actor.pk:
        return None
    notification = Notification.objects.create(
        recipient=recipient,
        actor=actor,
        kind=kind,
        message=message,
        post=post,
    )
    channel_layer = get_channel_layer()
    if channel_layer is not None:
        async_to_sync(channel_layer.group_send)(
            f"notifications_{recipient.pk}",
            {
                "type": "notification.message",
                "notification": {
                    "id": notification.pk,
                    "message": notification.message,
                    "kind": notification.kind,
                    "actor": notification.actor.username,
                    "created_at": notification.created_at.isoformat(),
                },
            },
        )
    return notification

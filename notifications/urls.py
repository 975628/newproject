from django.urls import path

from . import views


urlpatterns = [
    path("", views.inbox, name="notifications"),
    path("<int:notification_id>/read/", views.mark_read, name="mark_notification_read"),
]

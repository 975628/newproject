from django.urls import path

from . import views


urlpatterns = [
    path("", views.friend_center, name="friends"),
    path("<int:user_id>/follow/", views.follow_user, name="follow_user"),
    path("<int:user_id>/request/", views.send_friend_request, name="send_friend_request"),
    path(
        "request/<int:request_id>/respond/",
        views.respond_friend_request,
        name="respond_friend_request",
    ),
    path("<int:user_id>/block/", views.block_user, name="block_user"),
    path("<int:user_id>/unblock/", views.unblock_user, name="unblock_user"),
]

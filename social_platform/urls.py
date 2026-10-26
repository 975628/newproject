from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    CommentViewSet,
    FollowViewSet,
    FriendRequestViewSet,
    NotificationViewSet,
    PostViewSet,
    ProfileDetailView,
)
from users.forms import LoginForm

api_router = DefaultRouter()
api_router.register("posts", PostViewSet, basename="api-post")
api_router.register("comments", CommentViewSet, basename="api-comment")
api_router.register("follows", FollowViewSet, basename="api-follow")
api_router.register(
    "friend-requests", FriendRequestViewSet, basename="api-friend-request"
)
api_router.register("notifications", NotificationViewSet, basename="api-notification")


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            form_class=LoginForm, template_name="login.html"
        ),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("users.urls")),
    path("posts/", include("posts.urls")),
    path("friends/", include("friends.urls")),
    path("notifications/", include("notifications.urls")),
    path("api/", include(api_router.urls)),
    path("api/profiles/<str:username>/", ProfileDetailView.as_view(), name="api-profile"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

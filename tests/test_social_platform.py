from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase, override_settings
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from PIL import Image
from django.urls import reverse
from rest_framework.test import APIClient

from friends.models import Block, Follow, FriendRequest
from notifications.models import Notification
from notifications.consumers import NotificationConsumer
from posts.models import Post


class SocialPlatformTests(TestCase):
    def setUp(self):
        self.alex = User.objects.create_user("alex", password="test-password-123")
        self.sam = User.objects.create_user("sam", password="test-password-123")

    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome back")

    def test_registration_creates_profile_and_logs_in(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "new-user",
                "email": "new@example.com",
                "password1": "S0mething-secure-123",
                "password2": "S0mething-secure-123",
            },
        )
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(User.objects.get(username="new-user").profile)

    def test_feed_shows_only_posts_visible_to_user(self):
        public_post = Post.objects.create(
            author=self.alex, content="hello everyone", audience="public"
        )
        followers_post = Post.objects.create(
            author=self.alex, content="hello followers", audience="followers"
        )
        self.client.force_login(self.sam)
        response = self.client.get(reverse("home"))
        self.assertContains(response, public_post.content)
        self.assertNotContains(response, followers_post.content)

        Follow.objects.create(from_user=self.sam, to_user=self.alex)
        response = self.client.get(reverse("home"))
        self.assertContains(response, followers_post.content)

    def test_block_hides_posts_and_profiles(self):
        post = Post.objects.create(author=self.alex, content="blocked post")
        Block.objects.create(blocker=self.alex, blocked=self.sam)
        self.client.force_login(self.sam)
        self.assertNotContains(self.client.get(reverse("home")), post.content)
        response = self.client.get(
            reverse("profile", kwargs={"username": self.alex.username})
        )
        self.assertRedirects(response, reverse("home"))

    def test_like_creates_single_notification_and_can_be_removed(self):
        post = Post.objects.create(author=self.alex, content="like me")
        self.client.force_login(self.sam)
        like_url = reverse("toggle_like", kwargs={"post_id": post.pk})
        self.client.post(like_url)
        self.client.post(like_url)
        self.assertEqual(post.likes.count(), 0)
        self.assertEqual(
            Notification.objects.filter(recipient=self.alex, kind="like").count(), 1
        )

    def test_temporary_post_image_upload_is_served(self):
        image_buffer = BytesIO()
        Image.new("RGB", (2, 2), color="blue").save(image_buffer, format="PNG")
        image_buffer.seek(0)

        with TemporaryDirectory() as media_root:
            with override_settings(
                MEDIA_ROOT=media_root,
                SERVE_MEDIA_FILES=True,
            ):
                self.client.force_login(self.alex)
                response = self.client.post(
                    reverse("home"),
                    {
                        "content": "Temporary photo",
                        "audience": "public",
                        "comments_enabled": "on",
                        "image": SimpleUploadedFile(
                            "temporary.png", image_buffer.read(), content_type="image/png"
                        ),
                    },
                )
                self.assertRedirects(response, reverse("home"))
                post = Post.objects.get(author=self.alex)
                image_response = self.client.get(post.image.url)
                self.assertEqual(image_response.status_code, 200)
                self.assertEqual(image_response["Content-Type"], "image/png")
                self.assertTrue(b"".join(image_response.streaming_content))

    def test_friend_request_can_be_accepted(self):
        self.client.force_login(self.sam)
        self.client.post(
            reverse("send_friend_request", kwargs={"user_id": self.alex.pk})
        )
        request = FriendRequest.objects.get(sender=self.sam, receiver=self.alex)
        self.client.force_login(self.alex)
        response = self.client.post(
            reverse("respond_friend_request", kwargs={"request_id": request.pk}),
            {"action": "accept"},
        )
        self.assertRedirects(response, reverse("friends"))
        request.refresh_from_db()
        self.assertEqual(request.status, "accepted")


class SocialApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("api-user", password="test-password-123")
        self.client = APIClient()

    def test_authenticated_user_can_create_and_like_post(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            "/api/posts/",
            {"content": "Created using API", "audience": "public"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        post_id = response.data["id"]
        response = self.client.post(f"/api/posts/{post_id}/like/", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["liked"])

    def test_anonymous_api_cannot_create_post(self):
        response = self.client.post(
            "/api/posts/", {"content": "Not allowed"}, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_api_rejects_empty_post(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            "/api/posts/", {"content": "", "audience": "public"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_api_friend_request_can_be_accepted(self):
        other = User.objects.create_user("other", password="test-password-123")
        self.client.force_authenticate(self.user)
        response = self.client.post(
            "/api/friend-requests/",
            {"receiver_id": other.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        request_id = response.data["id"]

        self.client.force_authenticate(other)
        response = self.client.post(
            f"/api/friend-requests/{request_id}/respond/",
            {"action": "accept"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], "accepted")


class NotificationWebSocketTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user("socket-user", password="test-password-123")

    async def test_authenticated_user_receives_notification_event(self):
        consumer = NotificationConsumer.as_asgi()

        async def authenticated_consumer(scope, receive, send):
            scope["user"] = self.user
            await consumer(scope, receive, send)

        communicator = WebsocketCommunicator(
            authenticated_consumer, "/ws/notifications/"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await get_channel_layer().group_send(
            f"notifications_{self.user.pk}",
            {
                "type": "notification.message",
                "notification": {"message": "A live update"},
            },
        )
        self.assertEqual(
            await communicator.receive_json_from(timeout=1),
            {"message": "A live update"},
        )
        await communicator.disconnect()

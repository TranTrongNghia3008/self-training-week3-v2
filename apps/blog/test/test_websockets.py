import json
import asyncio
import websockets
from channels.testing import ChannelsLiveServerTestCase
from asgiref.sync import sync_to_async
from apps.users.test.factories import UserFactory
from apps.blog.test.factories import PostFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

class WebSocketCommentNotificationTests(ChannelsLiveServerTestCase):
    def setUp(self):
        self.user = UserFactory()
        self.other_user = UserFactory()
        self.post = PostFactory(author=self.other_user)
        self.post_ws = None
        self.notify_ws = None

        # Đăng nhập user
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    async def asyncTearDown(self):
        if self.post_ws:
            await self.post_ws.close()
        if self.notify_ws:
            await self.notify_ws.close()

    async def test_create_update_delete_comment_and_ws_notifications(self):
        post_url = f"{self.live_server_ws_url}/ws/posts/{self.post.id}/"
        notify_url = f"{self.live_server_ws_url}/ws/notifications/{self.other_user.id}/"

        self.post_ws = await websockets.connect(post_url)
        self.notify_ws = await websockets.connect(notify_url)

        # --- Create ---
        content = "This is a test comment via WS"
        response = await sync_to_async(self.client.post)(f"/api/blog/posts/{self.post.id}/comments/", {
            "content": content,
        }, format="json")

        self.assertEqual(response.status_code, 201)
        comment_id = response.data["id"]

        await asyncio.sleep(0.5)

        # Nhận từ post_ws
        post_created_raw = await asyncio.wait_for(self.post_ws.recv(), timeout=5)
        post_created_data = json.loads(post_created_raw)
        print("Post WS - Created:", post_created_data)
        self.assertEqual(post_created_data["action"], "created")
        self.assertEqual(post_created_data["comment"]["content"], content)
        self.assertEqual(post_created_data["comment"]["author"], self.user.username)

        # Nhận từ notify_ws
        notify_created_raw = await asyncio.wait_for(self.notify_ws.recv(), timeout=5)
        notify_created_data = json.loads(notify_created_raw)
        print("Notify WS - Created:", notify_created_data)
        self.assertIn(self.user.username, notify_created_data["message"])
        self.assertEqual(notify_created_data["object_id"], self.post.id)

        # --- Update ---
        updated_content = "Updated comment content"
        response = await sync_to_async(self.client.patch)(f"/api/blog/comments/{comment_id}/", {
            "content": updated_content
        }, format="json")

        self.assertEqual(response.status_code, 200)

        await asyncio.sleep(0.5)

        post_updated_raw = await asyncio.wait_for(self.post_ws.recv(), timeout=5)
        post_updated_data = json.loads(post_updated_raw)
        print("Post WS - Updated:", post_updated_data)
        self.assertEqual(post_updated_data["action"], "updated")
        self.assertEqual(post_updated_data["comment"]["id"], comment_id)
        self.assertEqual(post_updated_data["comment"]["content"], updated_content)

        # --- Delete ---
        response = await sync_to_async(self.client.delete)(f"/api/blog/comments/{comment_id}/")
        self.assertEqual(response.status_code, 204)

        await asyncio.sleep(0.5)

        post_deleted_raw = await asyncio.wait_for(self.post_ws.recv(), timeout=5)
        post_deleted_data = json.loads(post_deleted_raw)
        print("Post WS - Deleted:", post_deleted_data)
        self.assertEqual(post_deleted_data["action"], "deleted")
        self.assertEqual(post_deleted_data["comment_id"], comment_id)

        await self.post_ws.close()
        await self.notify_ws.close()
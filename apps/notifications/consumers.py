# apps/notifications/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from apps.notifications.models import Notification

User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.room_group_name = f"notify_{self.user_id}"
        print(f"[NotificationConsumer] User connected to notifications for user_id={self.user_id}, group: {self.room_group_name}")
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        print(f"[NotificationConsumer] User disconnected from notifications for user_id={self.user_id}, group: {self.room_group_name}")
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def notification_event(self, event):
        print(f"[NotificationConsumer] Sending notification event to user_id={self.user_id}: {event['data']}")
        await self.send(text_data=json.dumps(event["data"]))

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.post_id = self.scope["url_route"]["kwargs"]["post_id"]
        self.room_group_name = f"post_{self.post_id}"
        print(f"[CommentConsumer] Connected to post {self.post_id}, group: {self.room_group_name}")
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        print(f"[CommentConsumer] Disconnected from post {self.post_id}")
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        print(f"[CommentConsumer] Ignoring client message: {text_data}")

    async def comment_event(self, event):
        await self.send(text_data=json.dumps(event["data"]))

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework_simplejwt.tokens import AccessToken

from chat.models import Thread, Message, Friendship

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.thread_id = self.scope["url_route"]["kwargs"]["thread_id"]
        self.thread_group_name = f"chat_{self.thread_id}"

        query_params = self.scope["query_string"].decode()
        token_key = query_params.split("token=")[1] if "token=" in query_params else None

        if not token_key:
            await self.close(code=403)
            return

        self.user = await self.get_user_from_token(token_key)
        if not self.user:
            await self.close(code=403)
            return

        allowed = await self.user_in_thread()
        if not allowed:
            await self.close(code=403)
            return

        await self.channel_layer.group_add(self.thread_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "thread_group_name"):
            await self.channel_layer.group_discard(self.thread_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "")
        if not message:
            return

        saved_message = await self.create_message(message)

        if saved_message is None:
            await self.send(text_data=json.dumps({
                "type": "limit_reached",
                "message": "You’ve reached the 20-message limit. Add this user as a friend to continue chatting."
            }))
            return

        await self.channel_layer.group_send(
            self.thread_group_name,
            {
                "type": "chat.message",
                "message": saved_message["message"],
                "sender": saved_message["sender"],
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_user_from_token(self, token_key):
        try:
            access_token = AccessToken(token_key)
            user_id = access_token["user_id"]
            return User.objects.get(id=user_id)
        except Exception:
            return None

    @database_sync_to_async
    def user_in_thread(self):
        try:
            thread = Thread.objects.get(id=self.thread_id)
            return thread.user1 == self.user or thread.user2 == self.user
        except Thread.DoesNotExist:
            return False

    @database_sync_to_async
    def create_message(self, message):
        thread = Thread.objects.get(id=self.thread_id)
        receiver = thread.user2 if thread.user1 == self.user else thread.user1

        # Check friendship
        is_friend = Friendship.objects.filter(
            (Q(user=self.user, friend=receiver) | Q(user=receiver, friend=self.user))
        ).exists()

        # Enforce message limit for non-friends
        if not is_friend:
            count = Message.objects.filter(thread=thread).count()
            if count >= 20:
                return None  # stop here

        msg = Message.objects.create(thread=thread, sender=self.user, content=message)
        return {"message": msg.content, "sender": self.user.username}

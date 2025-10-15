from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from chat.models import Thread, Message, Friendship
from rest_framework_simplejwt.tokens import UntypedToken
from django.contrib.auth.models import AnonymousUser
from jwt import decode as jwt_decode
from django.conf import settings

User = get_user_model()


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # JWT token from query params ?token=...
        self.user = await self.get_user_from_token(self.scope['query_string'])
        if self.user is None or isinstance(self.user, AnonymousUser):
            await self.close()
            return

        self.thread_id = self.scope["url_route"]["kwargs"]["thread_id"]
        self.thread_group_name = f"thread_{self.thread_id}"

        # Permission check
        is_participant = await database_sync_to_async(self.is_participant)()
        if not is_participant:
            await self.close()
            return

        await self.channel_layer.group_add(self.thread_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.thread_group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        message_text = content.get("message")
        if not message_text:
            return

        # Check 20-message limit for non-friends
        can_send = await database_sync_to_async(self.check_message_limit)()
        if not can_send:
            await self.send_json({"error": "Message limit reached for non-friends"})
            return

        # Save message
        msg = await database_sync_to_async(self.create_message)(message_text)

        # Broadcast
        await self.channel_layer.group_send(
            self.thread_group_name,
            {
                "type": "chat.message",
                "message": msg.content,
                "sender": msg.sender.username,
                "timestamp": str(msg.timestamp),
            }
        )

    async def chat_message(self, event):
        await self.send_json(event)

    # ---------- Helper Methods ----------
    async def get_user_from_token(self, query_string):
        from urllib.parse import parse_qs
        qs = parse_qs(query_string.decode())
        token = qs.get("token")
        if not token:
            return AnonymousUser()
        try:
            decoded = jwt_decode(token[0], settings.SECRET_KEY, algorithms=["HS256"])
            user = await database_sync_to_async(User.objects.get)(id=decoded["user_id"])
            return user
        except:
            return AnonymousUser()

    def is_participant(self):
        try:
            thread = Thread.objects.get(id=self.thread_id)
        except Thread.DoesNotExist:
            return False
        return thread.is_participant(self.user)

    def check_message_limit(self):
        thread = Thread.objects.get(id=self.thread_id)
        other_user = thread.get_other_user(self.user)
        if Friendship.are_friends(self.user, other_user):
            return True
        total_messages = Message.count_between_nonfriends(self.user, other_user)
        return total_messages < 20

    def create_message(self, message_text):
        thread = Thread.objects.get(id=self.thread_id)
        return Message.objects.create(thread=thread, sender=self.user, content=message_text)

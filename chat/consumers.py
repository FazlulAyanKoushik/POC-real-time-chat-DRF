from channels.generic.websocket import AsyncJsonWebsocketConsumer

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive_json(self, content, **kwargs):
        await self.send_json({"echo": content})

    async def disconnect(self, code):
        pass

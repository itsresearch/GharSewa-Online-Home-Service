import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ServiceProvider

class ServiceRequestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Add the channel to the service providers group
        await self.channel_layer.group_add(
            'service_providers',
            self.channel_name
        )
        await self.accept()
    
    async def disconnect(self, close_code):
        # Remove the channel from the service providers group
        await self.channel_layer.group_discard(
            'service_providers',
            self.channel_name
        )
    
    async def receive(self, text_data):
        # Handle any messages received from the WebSocket
        pass
    
    async def new_request(self, event):
        # Send the new request notification to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_request',
            'message': event['message']
        })) 
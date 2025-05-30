import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import ChatRoom, Message
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Handles the WebSocket connection.
        Authenticates the user and adds them to the appropriate chat room group.
        """
        # Get the room name from the URL route
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Accept the WebSocket connection
        await self.accept()

        # Get the current user
        self.user = self.scope["user"]

        # If user is not authenticated, close the connection
        if not self.user.is_authenticated:
            await self.close()
            return

        # Add the user to the channel layer group for the specific room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Fetch the ChatRoom instance
        self.chat_room = await sync_to_async(ChatRoom.objects.get)(name=self.room_name)

        # Send existing messages to the newly connected user
        messages = await sync_to_async(list)(
            self.chat_room.messages.order_by('-timestamp')[:50].select_related('sender')
        )
        # Reverse messages to display oldest first
        messages = messages[::-1]

        for message in messages:
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'message': message.content,
                'username': message.sender.username,
                'timestamp': message.timestamp.strftime('%H:%M'), # Format time
            }))

        # Notify other users in the room about the new online user
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_presence',
                'username': self.user.username,
                'status': 'online'
            }
        )

    async def disconnect(self, close_code):
        """
        Handles WebSocket disconnection.
        Removes the user from the chat room group.
        """
        # Remove user from the channel layer group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Notify other users in the room about the user going offline
        if self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_presence',
                    'username': self.user.username,
                    'status': 'offline'
                }
            )

    async def receive(self, text_data):
        """
        Receives messages from the WebSocket.
        Parses the message, saves it to the database, and sends it to the group.
        """
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = self.user.username # Get username from authenticated user

        # Save the message to the database asynchronously
        await sync_to_async(Message.objects.create)(
            room=self.chat_room,
            sender=self.user,
            content=message
        )

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message', # This calls the chat_message method below
                'message': message,
                'username': username,
                'timestamp': text_data_json.get('timestamp', '') # Use client timestamp or leave empty
            }
        )

    async def chat_message(self, event):
        """
        Receives messages from the channel layer group and sends them to the WebSocket.
        This method is called by `channel_layer.group_send` with type 'chat_message'.
        """
        message = event['message']
        username = event['username']
        timestamp = event.get('timestamp', '')

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'username': username,
            'timestamp': timestamp
        }))

    async def user_presence(self, event):
        """
        Handles user presence updates (online/offline).
        This method is called by `channel_layer.group_send` with type 'user_presence'.
        """
        username = event['username']
        status = event['status']

        # Send presence update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'user_presence',
            'username': username,
            'status': status
        }))

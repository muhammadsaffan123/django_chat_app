from django.urls import re_path

from . import consumers

# Defines the URL patterns for WebSocket connections.
# 'ws/chat/<room_name>/' will be routed to the ChatConsumer.
websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]

"""
ASGI config for chat_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_project.settings')

# Get Django's ASGI application first. This ensures Django's app registry is loaded.
django_asgi_app = get_asgi_application()

# Import your chat_app's routing *after* Django's ASGI app is initialized.
# This prevents the AppRegistryNotReady error.
import chat_app.routing

# Define the ProtocolTypeRouter to handle different protocols (HTTP, WebSocket)
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app, # HTTP requests handled by Django's WSGI application
        "websocket": AllowedHostsOriginValidator( # WebSocket requests
            AuthMiddlewareStack( # Authenticate users for WebSocket connections
                URLRouter(
                    chat_app.routing.websocket_urlpatterns # Route WebSocket URLs to consumers
                )
            )
        ),
    }
)

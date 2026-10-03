"""
ASGI config for charityshopbackend project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from django.conf import settings
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'charityshopbackend.settings')

django_asgi_app = get_asgi_application()

from charityshopbackend.routing import websocket_urlpatterns  # noqa: E402


def _websocket_allowed_origins():
    origins = set()
    for host in settings.ALLOWED_HOSTS:
        if host and host != '*':
            origins.add(f'http://{host}')
            origins.add(f'https://{host}')
    for origin in settings.CORS_ALLOWED_ORIGINS:
        origins.add(origin.rstrip('/'))
    return list(origins)


application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': OriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
        _websocket_allowed_origins(),
    ),
})

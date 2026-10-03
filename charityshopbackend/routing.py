from django.urls import path

from aiassistant.consumers import AiChatConsumer

websocket_urlpatterns = [
    path('ws/ai_assistant/chat/', AiChatConsumer.as_asgi()),
]

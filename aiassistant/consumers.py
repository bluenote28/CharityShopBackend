import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor

from channels.generic.websocket import AsyncWebsocketConsumer

from aiassistant.ai_client import ai_assistant_chat_stream

logger = logging.getLogger(__name__)

_stream_executor = ThreadPoolExecutor(max_workers=4)


class AiChatConsumer(AsyncWebsocketConsumer):
    """Stream AI assistant chat replies over a WebSocket channel."""

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            await self._send_json({
                'type': 'error',
                'detail': 'Invalid chat messages',
            })
            return

        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_json({
                'type': 'error',
                'detail': 'Invalid JSON',
            })
            return

        messages = payload.get('messages')
        if not isinstance(messages, list):
            await self._send_json({
                'type': 'error',
                'detail': 'Invalid chat messages',
            })
            return

        try:
            async for event in self._iter_stream_events(messages):
                await self._send_json(event)
        except Exception:
            logger.exception('Error streaming AI chat response')
            await self._send_json({
                'type': 'error',
                'detail': 'AI chat is unavailable',
            })

    async def _iter_stream_events(self, messages):
        loop = asyncio.get_running_loop()
        queue = asyncio.Queue()

        def produce():
            try:
                for event in ai_assistant_chat_stream(messages):
                    asyncio.run_coroutine_threadsafe(queue.put(event), loop).result()
            except Exception as exc:
                logger.exception('AI stream producer failed')
                asyncio.run_coroutine_threadsafe(
                    queue.put({'type': 'error', 'detail': str(exc) or 'AI chat is unavailable'}),
                    loop,
                ).result()
            finally:
                asyncio.run_coroutine_threadsafe(queue.put(None), loop).result()

        loop.run_in_executor(_stream_executor, produce)

        while True:
            event = await queue.get()
            if event is None:
                break
            yield event

    async def _send_json(self, payload):
        await self.send(text_data=json.dumps(payload))

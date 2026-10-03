import json
import unittest
from unittest.mock import Mock, patch

import requests
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase, override_settings
from rest_framework import status
from rest_framework.test import APIRequestFactory

from aiassistant.ai_client import (
    _error_detail,
    _message_text,
    ai_assistant_chat,
    ai_assistant_chat_stream,
    get_ai_advice,
)
from aiassistant.consumers import AiChatConsumer
from aiassistant.views import AiItemAssistantView
from charityshopbackend.asgi import application


def _item(name="Vintage Lamp", seller_description="Seller notes", charity_id=42):
    item = Mock()
    item.name = name
    item.seller_description = seller_description
    item.charity_id = charity_id
    return item


def _ok_response(content="A red lamp"):
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "choices": [{"message": {"content": content}, "finish_reason": "stop"}]
    }
    return mock_response


def _stream_response(chunks, ok=True, error_json=None):
    mock_response = Mock()
    mock_response.ok = ok
    if error_json is not None:
        mock_response.json.return_value = error_json

    lines = []
    for chunk in chunks:
        lines.append(f"data: {json.dumps(chunk)}")
    lines.append("data: [DONE]")

    mock_response.iter_lines.return_value = iter(lines)
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)
    return mock_response


class TestGetAiAdvice(unittest.TestCase):

    @patch("aiassistant.ai_client.caches")
    @patch("aiassistant.ai_client.Item.objects")
    @patch("aiassistant.ai_client.EbayClient")
    @patch("aiassistant.ai_client.requests.post")
    def test_returns_message_content(self, mock_post, mock_ebay_client, mock_items, mock_caches):
        item = _item()
        mock_items.get.return_value = item
        mock_post.return_value = _ok_response("A red lamp")

        result = get_ai_advice("123")

        self.assertEqual(result, {"description": "A red lamp"})
        mock_items.get.assert_called_with(ebay_id="123")
        mock_ebay_client.assert_not_called()
        self.assertEqual(item.ai_description, "A red lamp")
        item.save.assert_called_once()
        mock_caches.__getitem__.return_value.delete.assert_called_once_with("item_123")
        prompt = mock_post.call_args.kwargs["json"]["messages"][1]["content"]
        self.assertEqual(
            prompt,
            "Item name: Vintage Lamp, Seller description: Seller notes",
        )

    @patch("aiassistant.ai_client.caches")
    @patch("aiassistant.ai_client.Item.objects")
    @patch("aiassistant.ai_client.EbayClient")
    @patch("aiassistant.ai_client.requests.post")
    def test_fetches_seller_description_when_missing(self, mock_post, mock_ebay_client, mock_items, mock_caches):
        item = _item(seller_description=None)
        mock_items.get.return_value = item
        mock_ebay_client.return_value.getItemDetails.return_value = {
            "seller_description": "From eBay",
        }
        mock_post.return_value = _ok_response()

        get_ai_advice("123")

        mock_ebay_client.assert_called_once_with(42)
        mock_ebay_client.return_value.getItemDetails.assert_called_once_with("123")
        self.assertEqual(item.seller_description, "From eBay")
        prompt = mock_post.call_args.kwargs["json"]["messages"][1]["content"]
        self.assertIn("Seller description: From eBay", prompt)

    @patch("aiassistant.ai_client.Item.objects")
    @patch("aiassistant.ai_client.EbayClient")
    @patch("aiassistant.ai_client.requests.post")
    def test_http_error_returns_detail(self, mock_post, mock_ebay_client, mock_items):
        mock_items.get.return_value = _item()
        mock_response = Mock()
        mock_response.ok = False
        mock_response.json.return_value = {"error": "nope"}
        mock_post.return_value = mock_response

        self.assertEqual(get_ai_advice("123"), {"detail": "nope"})

    @patch("aiassistant.ai_client.Item.objects")
    @patch("aiassistant.ai_client.requests.post")
    def test_request_exception_returns_unavailable(self, mock_post, mock_items):
        mock_items.get.return_value = _item()
        mock_post.side_effect = requests.RequestException()

        self.assertEqual(
            get_ai_advice("123"),
            {"detail": "AI description is unavailable"},
        )

    @patch("aiassistant.ai_client.Item.objects")
    @patch("aiassistant.ai_client.requests.post")
    def test_empty_message_returns_unavailable(self, mock_post, mock_items):
        mock_items.get.return_value = _item()
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"choices": [{"message": {"content": ""}}]}
        mock_post.return_value = mock_response

        self.assertEqual(
            get_ai_advice("123"),
            {"detail": "AI description is unavailable"},
        )

    @patch("aiassistant.ai_client.caches")
    @patch("aiassistant.ai_client.Item.objects")
    @patch("aiassistant.ai_client.requests.post")
    def test_list_content_is_joined(self, mock_post, mock_items, mock_caches):
        mock_items.get.return_value = _item()
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{"message": {"content": ["Part A", "Part B"]}}]
        }
        mock_post.return_value = mock_response

        result = get_ai_advice("123")

        self.assertEqual(result, {"description": "Part APart B"})


class TestMessageText(unittest.TestCase):

    def test_non_dict_returns_empty(self):
        self.assertEqual(_message_text(None), "")
        self.assertEqual(_message_text("hello"), "")

    def test_strips_string_content(self):
        self.assertEqual(_message_text({"content": "  lamp  "}), "lamp")

    def test_empty_list_content_falls_through_to_text_key(self):
        self.assertEqual(_message_text({"content": [], "text": "fallback"}), "fallback")


class TestErrorDetail(unittest.TestCase):

    def test_dict_error_message(self):
        self.assertEqual(_error_detail({"error": {"message": "quota"}}), "quota")

    def test_dict_error_code(self):
        self.assertEqual(_error_detail({"error": {"code": "429"}}), "429")

    def test_string_error(self):
        self.assertEqual(_error_detail({"error": "nope"}), "nope")

    def test_missing_or_blank_error(self):
        self.assertIsNone(_error_detail({}))
        self.assertIsNone(_error_detail({"error": "  "}))
        self.assertIsNone(_error_detail("not a dict"))


class TestAiItemAssistantView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = AiItemAssistantView.as_view()

    @patch("aiassistant.views.get_ai_advice", return_value={"description": "nice"})
    def test_post_returns_description(self, mock_get):
        request = self.factory.post(
            "/api/ai_assistant/",
            {"ebay_id": "123"},
            format="json",
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"description": "nice"})
        mock_get.assert_called_once_with("123")

    def test_post_missing_ebay_id_returns_400(self):
        request = self.factory.post("/api/ai_assistant/", {}, format="json")
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "Missing eBay ID"})


class TestAiAssistantChat(unittest.TestCase):

    @patch("aiassistant.ai_client.requests.post")
    def test_returns_assistant_message(self, mock_post):
        mock_post.return_value = _ok_response("Try searching vintage lamps")
        result = ai_assistant_chat([{"role": "user", "content": "lamps"}])
        self.assertEqual(result, {"message": "Try searching vintage lamps"})
        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertFalse(payload["stream"])


class TestAiAssistantChatStream(unittest.TestCase):

    @patch("aiassistant.ai_client.requests.post")
    def test_streams_tokens_then_done(self, mock_post):
        mock_post.return_value = _stream_response([
            {"choices": [{"delta": {"content": "Hello"}, "finish_reason": None}]},
            {"choices": [{"delta": {"content": " world"}, "finish_reason": "stop"}]},
        ])

        events = list(ai_assistant_chat_stream([{"role": "user", "content": "hi"}]))

        self.assertEqual(
            events,
            [
                {"type": "token", "content": "Hello"},
                {"type": "token", "content": " world"},
                {"type": "done"},
            ],
        )
        self.assertTrue(mock_post.call_args.kwargs["json"]["stream"])

    @patch("aiassistant.ai_client.search_items", return_value='[{"name": "Mug"}]')
    @patch("aiassistant.ai_client.requests.post")
    def test_tool_calls_then_streams_final_reply(self, mock_post, mock_search):
        tool_stream = _stream_response([
            {
                "choices": [{
                    "delta": {
                        "tool_calls": [{
                            "index": 0,
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "search_items",
                                "arguments": '{"query":"mug"}',
                            },
                        }]
                    },
                    "finish_reason": "tool_calls",
                }]
            },
        ])
        final_stream = _stream_response([
            {"choices": [{"delta": {"content": "Found a mug"}, "finish_reason": "stop"}]},
        ])
        mock_post.side_effect = [tool_stream, final_stream]

        events = list(ai_assistant_chat_stream([{"role": "user", "content": "mug"}]))

        self.assertEqual(
            events,
            [
                {"type": "token", "content": "Found a mug"},
                {"type": "done"},
            ],
        )
        mock_search.assert_called_once_with({"query": "mug"})
        self.assertEqual(mock_post.call_count, 2)


@override_settings(
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}},
    ALLOWED_HOSTS=["localhost", "testserver", "127.0.0.1"],
)
class TestAiChatConsumer(TransactionTestCase):

    async def test_streams_chat_over_websocket(self):
        communicator = WebsocketCommunicator(
            application,
            "/ws/ai_assistant/chat/",
            headers=[(b"origin", b"http://localhost")],
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        with patch(
            "aiassistant.consumers.ai_assistant_chat_stream",
            return_value=iter([
                {"type": "token", "content": "Hi"},
                {"type": "done"},
            ]),
        ):
            await communicator.send_json_to({
                "messages": [{"role": "user", "content": "hello"}],
            })
            first = await communicator.receive_json_from()
            second = await communicator.receive_json_from()

        self.assertEqual(first, {"type": "token", "content": "Hi"})
        self.assertEqual(second, {"type": "done"})
        await communicator.disconnect()

    async def test_invalid_messages_returns_error(self):
        communicator = WebsocketCommunicator(AiChatConsumer.as_asgi(), "/ws/ai_assistant/chat/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to({"messages": "not-a-list"})
        response = await communicator.receive_json_from()

        self.assertEqual(response, {"type": "error", "detail": "Invalid chat messages"})
        await communicator.disconnect()

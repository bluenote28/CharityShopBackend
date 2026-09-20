import unittest
from unittest.mock import Mock, patch

import requests
from rest_framework import status
from rest_framework.test import APIRequestFactory

from aiassistant.ai_client import _error_detail, _message_text, get_ai_advice, get_ai_chat_reply, normalize_chat_messages
from aiassistant.views import AiChatView, AiItemAssistantView


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
        "choices": [{"message": {"content": content}}]
    }
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
        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["max_completion_tokens"], 1024)

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
    def test_invalid_json_returns_unavailable(self, mock_post, mock_items):
        mock_items.get.return_value = _item()
        mock_response = Mock()
        mock_response.json.side_effect = ValueError()
        mock_post.return_value = mock_response

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

    @patch("aiassistant.ai_client.Item.objects")
    @patch("aiassistant.ai_client.requests.post")
    def test_http_error_without_error_field_returns_unavailable(self, mock_post, mock_items):
        mock_items.get.return_value = _item()
        mock_response = Mock()
        mock_response.ok = False
        mock_response.json.return_value = {}
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

    @patch("aiassistant.ai_client.caches")
    @patch("aiassistant.ai_client.Item.objects")
    @patch("aiassistant.ai_client.requests.post")
    def test_text_parts_in_content_list(self, mock_post, mock_items, mock_caches):
        mock_items.get.return_value = _item()
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": [
                        {"type": "text", "text": "Hello "},
                        {"type": "output_text", "content": "world"},
                    ]
                }
            }]
        }
        mock_post.return_value = mock_response

        self.assertEqual(get_ai_advice("123"), {"description": "Hello world"})

    @patch("aiassistant.ai_client.caches")
    @patch("aiassistant.ai_client.Item.objects")
    @patch("aiassistant.ai_client.requests.post")
    def test_output_text_fallback(self, mock_post, mock_items, mock_caches):
        mock_items.get.return_value = _item()
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{"message": {"output_text": "From output_text"}}]
        }
        mock_post.return_value = mock_response

        self.assertEqual(get_ai_advice("123"), {"description": "From output_text"})


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


class TestNormalizeChatMessages(unittest.TestCase):

    def test_requires_user_last_message(self):
        self.assertIsNone(normalize_chat_messages([
            {"role": "assistant", "content": "Hello"},
        ]))

    def test_trims_and_keeps_user_message(self):
        self.assertEqual(
            normalize_chat_messages([{"role": "user", "content": "  lamps  "}]),
            [{"role": "user", "content": "lamps"}],
        )


class TestGetAiChatReply(unittest.TestCase):

    @patch("aiassistant.ai_client.requests.post")
    def test_returns_assistant_message(self, mock_post):
        mock_post.return_value = _ok_response("Try searching vintage lamps")
        result = get_ai_chat_reply(
            [{"role": "user", "content": "lamps"}],
            page_context={"path": "/search", "search": "?q=lamp"},
        )
        self.assertEqual(result, {"message": "Try searching vintage lamps"})
        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertIn("/search?q=lamp", payload["messages"][0]["content"])
        self.assertNotIn("thinking", payload)


class TestAiChatView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = AiChatView.as_view()

    @patch("aiassistant.views.get_ai_chat_reply", return_value={"message": "hello"})
    def test_post_returns_message(self, mock_chat):
        request = self.factory.post(
            "/api/ai_assistant/chat/",
            {"messages": [{"role": "user", "content": "hi"}], "page_context": "/"},
            format="json",
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "hello"})
        mock_chat.assert_called_once_with(
            [{"role": "user", "content": "hi"}],
            page_context="/",
        )

    def test_post_invalid_messages_returns_400(self):
        request = self.factory.post("/api/ai_assistant/chat/", {}, format="json")
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "Invalid chat messages"})

import unittest
from unittest.mock import Mock, patch
from rest_framework import status
from rest_framework.test import APIRequestFactory

from aiassistant.ai_client import get_item_description
from aiassistant.views import AiItemAssistantView


class TestGetItemDescription(unittest.TestCase):

    @patch("aiassistant.ai_client.Item.objects")
    @patch("aiassistant.ai_client.requests.post")
    def test_returns_message_content(self, mock_post, mock_items):
        mock_items.filter.return_value.values_list.return_value.first.return_value = None
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "A red lamp"}}]
        }
        mock_post.return_value = mock_response

        result = get_item_description(
            "https://www.ebay.com/itm/123",
            ebay_id="123",
        )

        self.assertEqual(result, {"description": "A red lamp"})
        mock_items.filter.assert_called_with(ebay_id="123")
        prompt = mock_post.call_args.kwargs["json"]["messages"][1]["content"]
        self.assertIn("eBay item ID: 123", prompt)

    @patch("aiassistant.ai_client.Item.objects")
    @patch("aiassistant.ai_client.requests.post")
    def test_blank_stored_description_calls_model(self, mock_post, mock_items):
        mock_items.filter.return_value.values_list.return_value.first.return_value = "   "
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "A red lamp"}}]
        }
        mock_post.return_value = mock_response

        result = get_item_description(
            "https://www.ebay.com/itm/123",
            ebay_id="123",
        )

        self.assertEqual(result, {"description": "A red lamp"})
        mock_post.assert_called_once()

    @patch("aiassistant.ai_client.Item.objects")
    @patch("aiassistant.ai_client.requests.post")
    def test_returns_stored_description_without_model_call(self, mock_post, mock_items):
        mock_items.filter.return_value.values_list.return_value.first.return_value = (
            "Cached lamp description"
        )

        result = get_item_description(
            "https://www.ebay.com/itm/123",
            ebay_id="123",
        )

        self.assertEqual(result, {"description": "Cached lamp description"})
        mock_post.assert_not_called()
        mock_items.filter.return_value.update.assert_not_called()

    @patch("aiassistant.ai_client.requests.post")
    def test_http_error_returns_detail(self, mock_post):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.json.return_value = {"error": "nope"}
        mock_post.return_value = mock_response

        self.assertEqual(
            get_item_description("https://www.ebay.com/itm/123"),
            {"detail": "nope"},
        )


class TestAiItemAssistantView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = AiItemAssistantView.as_view()

    @patch("aiassistant.views.get_item_description", return_value={"description": "nice"})
    def test_post_returns_description(self, mock_get):
        request = self.factory.post(
            "/api/ai_assistant/",
            {
                "ebay_id": "123",
                "item_link": "https://www.ebay.com/itm/123",
            },
            format="json",
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"description": "nice"})
        mock_get.assert_called_once_with(
            "https://www.ebay.com/itm/123",
            item_name=None,
            ebay_id="123",
        )

    @patch("aiassistant.views.get_item_description", return_value={"description": "nice"})
    def test_post_builds_link_from_ebay_id(self, mock_get):
        request = self.factory.post(
            "/api/ai_assistant/",
            {"ebay_id": "123"},
            format="json",
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_get.assert_called_once_with(
            "https://www.ebay.com/itm/123",
            item_name=None,
            ebay_id="123",
        )

    def test_post_missing_ebay_id_returns_400(self):
        request = self.factory.post(
            "/api/ai_assistant/",
            {"item_link": "https://www.ebay.com/itm/123"},
            format="json",
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

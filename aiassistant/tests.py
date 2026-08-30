import unittest
from unittest.mock import Mock, patch
from rest_framework import status
from rest_framework.test import APIRequestFactory

from aiassistant.bedrock_client import get_item_description
from aiassistant.views import AiItemAssistantView


class TestGetItemDescription(unittest.TestCase):

    @patch("aiassistant.bedrock_client.client")
    def test_returns_model_json(self, mock_client):
        response = Mock()
        response.json.return_value = {"summary": "A red lamp"}
        mock_client.converse.return_value = response
        mock_client.exceptions.AccessDeniedException = type("AccessDeniedException", (Exception,), {})

        result = get_item_description("Red vintage lamp")

        self.assertEqual(result, {"summary": "A red lamp"})
        mock_client.converse.assert_called_once()

    @patch("aiassistant.bedrock_client.client")
    def test_access_denied_returns_error(self, mock_client):
        access_denied = type("AccessDeniedException", (Exception,), {})
        mock_client.exceptions.AccessDeniedException = access_denied
        mock_client.converse.side_effect = access_denied()

        self.assertEqual(get_item_description("lamp"), "error")

    @patch("aiassistant.bedrock_client.client")
    def test_generic_exception_returns_error(self, mock_client):
        mock_client.exceptions.AccessDeniedException = type("AccessDeniedException", (Exception,), {})
        mock_client.converse.side_effect = Exception("timeout")

        self.assertEqual(get_item_description("lamp"), "error")


class TestAiItemAssistantView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = AiItemAssistantView.as_view()

    @patch("aiassistant.views.get_item_description", return_value={"summary": "nice"})
    def test_post_returns_description(self, mock_get):
        request = self.factory.post("/api/ai_assistant/", {"item_name": "lamp"}, format="json")
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"summary": "nice"})
        mock_get.assert_called_once_with("lamp")

    def test_init_creates_instance(self):
        self.assertIsInstance(AiItemAssistantView(), AiItemAssistantView)

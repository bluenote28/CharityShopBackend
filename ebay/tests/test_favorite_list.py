import unittest
from unittest.mock import Mock, patch
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from django.contrib.auth.models import User as DjangoUser
from ebay.views.favorite_list import FavoriteListView


class TestFavoriteListGet(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = FavoriteListView.as_view()
        self.user = Mock(spec=DjangoUser)
        self.user.id = 1
        self.user.is_authenticated = True

    @patch("ebay.views.favorite_list.FavoriteListSerializer")
    @patch("ebay.views.favorite_list.FavoriteList")
    @patch("ebay.views.favorite_list.User")
    def test_get_returns_favorite_list(self, mock_user_model, mock_favorite_list_model, mock_serializer):
        mock_user_model.objects.get.return_value = self.user
        favorite_list = Mock()
        queryset = Mock()
        queryset.get.return_value = favorite_list
        mock_favorite_list_model.objects.prefetch_related.return_value = queryset
        mock_serializer.return_value.data = {"items": [], "charities": []}

        request = self.factory.get("/api/favorites/")
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_user_model.objects.get.assert_called_once_with(username=self.user)
        mock_favorite_list_model.objects.prefetch_related.assert_called_once_with("items", "charities")


class TestFavoriteListPost(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = FavoriteListView.as_view()
        self.user = Mock(spec=DjangoUser)
        self.user.id = 1
        self.user.is_authenticated = True

    def _mock_favorite_list(self, mock_favorite_list_model):
        favorite_list = Mock()
        favorite_list.items = Mock()
        favorite_list.charities = Mock()
        queryset = Mock()
        queryset.get.return_value = favorite_list
        mock_favorite_list_model.objects.prefetch_related.return_value = queryset
        return favorite_list

    @patch("ebay.views.favorite_list.FavoriteListSerializer")
    @patch("ebay.views.favorite_list.Item")
    @patch("ebay.views.favorite_list.FavoriteList")
    def test_post_adds_item(self, mock_favorite_list_model, mock_item_model, mock_serializer):
        favorite_list = self._mock_favorite_list(mock_favorite_list_model)
        item = Mock()
        mock_item_model.objects.get.return_value = item
        mock_serializer.return_value.data = {"items": ["ebay123"]}

        request = self.factory.post("/api/favorites/", {"item": "ebay123", "charity": ""}, format="json")
        force_authenticate(request, user=self.user)
        response = self.view(request)

        mock_item_model.objects.get.assert_called_once_with(ebay_id="ebay123")
        favorite_list.items.add.assert_called_once_with(item)
        favorite_list.save.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("ebay.views.favorite_list.CharitySerializer")
    @patch("ebay.views.favorite_list.FavoriteListSerializer")
    @patch("ebay.views.favorite_list.FavoriteList")
    def test_post_adds_valid_charity(self, mock_favorite_list_model, mock_serializer, mock_charity_serializer):
        favorite_list = self._mock_favorite_list(mock_favorite_list_model)
        mock_charity_serializer.return_value.is_valid.return_value = True
        mock_serializer.return_value.data = {"charities": [1]}

        request = self.factory.post(
            "/api/favorites/",
            {"item": "", "charity": {"id": 1, "name": "Good Cause"}},
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = self.view(request)

        favorite_list.charities.add.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("ebay.views.favorite_list.CharitySerializer")
    @patch("ebay.views.favorite_list.FavoriteListSerializer")
    @patch("ebay.views.favorite_list.FavoriteList")
    def test_post_ignores_invalid_charity(self, mock_favorite_list_model, mock_serializer, mock_charity_serializer):
        favorite_list = self._mock_favorite_list(mock_favorite_list_model)
        mock_charity_serializer.return_value.is_valid.return_value = False
        mock_serializer.return_value.data = {"charities": []}

        request = self.factory.post(
            "/api/favorites/",
            {"item": "", "charity": {"name": "Incomplete"}},
            format="json",
        )
        force_authenticate(request, user=self.user)
        self.view(request)

        favorite_list.charities.add.assert_not_called()


class TestFavoriteListDelete(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = FavoriteListView.as_view()
        self.user = Mock(spec=DjangoUser)
        self.user.id = 1
        self.user.is_authenticated = True

    def _mock_favorite_list(self, mock_favorite_list_model):
        favorite_list = Mock()
        favorite_list.items = Mock()
        favorite_list.charities = Mock()
        queryset = Mock()
        queryset.get.return_value = favorite_list
        mock_favorite_list_model.objects.prefetch_related.return_value = queryset
        return favorite_list

    def _mock_serializer(self, mock_serializer):
        serializer_instance = Mock()
        serializer_instance.data = {"items": []}
        mock_serializer.return_value = serializer_instance

    @patch('ebay.views.favorite_list.FavoriteListSerializer')
    @patch('ebay.views.favorite_list.Item')
    @patch('ebay.views.favorite_list.FavoriteList')
    def test_delete_removes_item_from_query_params(self, mock_favorite_list_model, mock_item_model, mock_serializer):
        favorite_list = self._mock_favorite_list(mock_favorite_list_model)
        item = Mock()
        mock_item_model.objects.get.return_value = item
        self._mock_serializer(mock_serializer)

        request = self.factory.delete('/api/favorites/?item=ebay123')
        force_authenticate(request, user=self.user)
        response = self.view(request)

        mock_item_model.objects.get.assert_called_once_with(ebay_id='ebay123')
        favorite_list.items.remove.assert_called_once_with(item)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('ebay.views.favorite_list.FavoriteListSerializer')
    @patch('ebay.views.favorite_list.Item')
    @patch('ebay.views.favorite_list.FavoriteList')
    def test_delete_removes_item_from_body(self, mock_favorite_list_model, mock_item_model, mock_serializer):
        favorite_list = self._mock_favorite_list(mock_favorite_list_model)
        item = Mock()
        mock_item_model.objects.get.return_value = item
        self._mock_serializer(mock_serializer)

        request = self.factory.delete('/api/favorites/', {'item': 'ebay123'}, format='json')
        force_authenticate(request, user=self.user)
        response = self.view(request)

        mock_item_model.objects.get.assert_called_once_with(ebay_id='ebay123')
        favorite_list.items.remove.assert_called_once_with(item)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('ebay.views.favorite_list.FavoriteListSerializer')
    @patch('ebay.views.favorite_list.Item')
    @patch('ebay.views.favorite_list.FavoriteList')
    def test_delete_without_item_does_not_lookup_item(self, mock_favorite_list_model, mock_item_model, mock_serializer):
        self._mock_favorite_list(mock_favorite_list_model)
        self._mock_serializer(mock_serializer)

        request = self.factory.delete('/api/favorites/')
        force_authenticate(request, user=self.user)
        response = self.view(request)

        mock_item_model.objects.get.assert_not_called()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("ebay.views.favorite_list.FavoriteListSerializer")
    @patch("ebay.views.favorite_list.FavoriteList")
    def test_delete_removes_charity(self, mock_favorite_list_model, mock_serializer):
        favorite_list = self._mock_favorite_list(mock_favorite_list_model)
        self._mock_serializer(mock_serializer)

        request = self.factory.delete("/api/favorites/?charity=12")
        force_authenticate(request, user=self.user)
        response = self.view(request)

        favorite_list.charities.remove.assert_called_once_with("12")
        favorite_list.save.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_favorite_field_prefers_body_over_query(self):
        view = FavoriteListView()
        request = Mock()
        request.data = {"item": "body-item"}
        request.query_params = {"item": "query-item"}

        self.assertEqual(view._favorite_field(request, "item"), "body-item")

    def test_favorite_field_falls_back_to_query_params(self):
        view = FavoriteListView()
        request = Mock()
        request.data = {}
        request.query_params = {"item": "query-item"}

        self.assertEqual(view._favorite_field(request, "item"), "query-item")

    def test_favorite_field_returns_none_when_missing(self):
        view = FavoriteListView()
        request = Mock()
        request.data = None
        request.query_params = {}

        self.assertIsNone(view._favorite_field(request, "item"))

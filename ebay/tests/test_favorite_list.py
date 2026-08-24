import unittest
from unittest.mock import Mock, patch
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from django.contrib.auth.models import User as DjangoUser
from ebay.views.favorite_list import FavoriteListView


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

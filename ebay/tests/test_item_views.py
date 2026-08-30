import unittest
from unittest.mock import Mock, patch
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from ebay.views.item_views import EbayCharityItems


class TestEbayCharityItemsGet(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayCharityItems.as_view()
        self.disk_patcher = patch("ebay.views.item_views.disk")
        self.mock_disk = self.disk_patcher.start()
        self.mock_disk.get.return_value = None

    def tearDown(self):
        self.disk_patcher.stop()

    def test_returns_400_without_params(self):
        request = self.factory.get("/api/items/ebaycharityitems/")
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            "Please provide an item_id, search_text, or category_id",
        )

    def test_item_cache_hit(self):
        cached = {"ebay_id": "ABC", "name": "Cached"}
        self.mock_disk.get.return_value = cached

        request = self.factory.get("/api/items/ebaycharityitems/ABC")
        response = self.view(request, item_id="ABC")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, cached)
        self.mock_disk.get.assert_called_once_with("item_ABC")

    @patch("ebay.views.item_views.retrieveItem")
    def test_item_not_found(self, mock_retrieve):
        mock_retrieve.return_value = None

        request = self.factory.get("/api/items/ebaycharityitems/MISSING")
        response = self.view(request, item_id="MISSING")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, "Item not found")

    @patch("ebay.views.item_views.ItemSerializer")
    @patch("ebay.views.item_views.retrieveItem")
    def test_item_with_existing_donation_percentage(self, mock_retrieve, mock_serializer):
        item = Mock()
        item.donation_percentage = 15.0
        mock_retrieve.return_value = item
        mock_serializer.return_value.data = {"ebay_id": "ABC"}

        request = self.factory.get("/api/items/ebaycharityitems/ABC")
        response = self.view(request, item_id="ABC")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.save.assert_not_called()
        self.mock_disk.set.assert_called_once()

    @patch("ebay.views.item_views.ebay_client.EbayClient")
    @patch("ebay.views.item_views.ItemSerializer")
    @patch("ebay.views.item_views.retrieveItem")
    def test_item_fetches_details_when_donation_missing(
        self, mock_retrieve, mock_serializer, mock_client_class
    ):
        item = Mock()
        item.donation_percentage = None
        mock_retrieve.return_value = item
        mock_client_class.return_value.getItemDetails.return_value = {
            "donation_percentage": "10.0",
            "seller_description": "A nice lamp",
        }
        mock_serializer.return_value.data = {"ebay_id": "ABC"}

        request = self.factory.get("/api/items/ebaycharityitems/ABC")
        response = self.view(request, item_id="ABC")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(item.donation_percentage, "10.0")
        self.assertEqual(item.seller_description, "A nice lamp")
        item.save.assert_called_once()

    def test_search_cache_hit(self):
        cached = {"results": []}
        self.mock_disk.get.return_value = cached

        request = self.factory.get("/api/items/ebaycharityitems/search/lamp?page=2")
        response = self.view(request, search_text="lamp")

        self.assertEqual(response.data, cached)
        self.mock_disk.get.assert_called_once_with("items_search_lamp_p2")

    @patch("ebay.views.item_views.ItemSerializer")
    @patch("ebay.views.item_views.search")
    def test_search_cache_miss_paginates(self, mock_search, mock_serializer):
        mock_search.return_value = [Mock(), Mock()]
        mock_serializer.return_value.data = [{"id": 1}, {"id": 2}]

        request = self.factory.get("/api/items/ebaycharityitems/search/lamp")
        with patch.object(EbayCharityItems, "paginator") as mock_paginator:
            mock_paginator.paginate_queryset.return_value = [Mock()]
            mock_paginator.get_paginated_response.return_value = Response(
                {"count": 1, "results": [{"id": 1}]}
            )
            response = self.view(request, search_text="lamp")

        mock_search.assert_called_once_with("lamp")
        self.assertEqual(response.data["count"], 1)
        self.mock_disk.set.assert_called_once()

    def test_category_cache_hit(self):
        cached = {"results": []}
        self.mock_disk.get.return_value = cached

        request = self.factory.get("/api/items/ebaycharityitems/category/Books")
        response = self.view(request, category_id="Books")

        self.assertEqual(response.data, cached)
        self.mock_disk.get.assert_called_once_with("items_cat_Books_p1")

    @patch("ebay.views.item_views.ItemSerializer")
    @patch("ebay.views.item_views.getItemsBySubCategory")
    def test_category_without_filter(self, mock_subcategory, mock_serializer):
        mock_subcategory.return_value = [Mock()]
        mock_serializer.return_value.data = [{"id": 1}]

        request = self.factory.get("/api/items/ebaycharityitems/category/Books")
        with patch.object(EbayCharityItems, "paginator") as mock_paginator:
            mock_paginator.paginate_queryset.return_value = [Mock()]
            mock_paginator.get_paginated_response.return_value = Response(
                {"count": 1, "results": [{"id": 1}]}
            )
            response = self.view(request, category_id="Books")

        mock_subcategory.assert_called_once_with("Books")
        self.assertEqual(response.data["count"], 1)

    def test_category_filter_cache_hit(self):
        cached = {"results": []}
        self.mock_disk.get.return_value = cached

        request = self.factory.get("/api/items/ebaycharityitems/category/Books/hardcover")
        response = self.view(request, category_id="Books", filter="hardcover")

        self.assertEqual(response.data, cached)
        self.mock_disk.get.assert_called_once_with("items_cat_Books_f_hardcover_p1")

    @patch("ebay.views.item_views.ItemSerializer")
    @patch("ebay.views.item_views.getItemsByFilter")
    def test_category_with_filter(self, mock_filter, mock_serializer):
        mock_filter.return_value = [Mock()]
        mock_serializer.return_value.data = [{"id": 1}]

        request = self.factory.get("/api/items/ebaycharityitems/category/Books/hardcover")
        with patch.object(EbayCharityItems, "paginator") as mock_paginator:
            mock_paginator.paginate_queryset.return_value = [Mock()]
            mock_paginator.get_paginated_response.return_value = Response(
                {"count": 1, "results": [{"id": 1}]}
            )
            response = self.view(request, category_id="Books", filter="hardcover")

        mock_filter.assert_called_once_with("Books", "hardcover")
        self.assertEqual(response.data["count"], 1)

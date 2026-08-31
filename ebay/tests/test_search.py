import unittest
from unittest.mock import MagicMock, patch

from ebay.search import search


class TestSearch(unittest.TestCase):

    def test_blank_query_returns_empty_queryset(self):
        with patch("ebay.search.Item") as mock_item:
            mock_item.objects.none.return_value = "empty"

            self.assertEqual(search(""), "empty")
            self.assertEqual(search("   "), "empty")
            self.assertEqual(search(None), "empty")
            mock_item.objects.filter.assert_not_called()

    @patch("ebay.search.SearchRank")
    @patch("ebay.search.SearchQuery")
    @patch("ebay.search.Item")
    def test_filters_persisted_search_vector(self, mock_item, mock_query, mock_rank):
        mock_query.return_value = "query-object"
        mock_rank.return_value = "rank-expr"
        queryset = MagicMock()
        mock_item.objects.filter.return_value = queryset
        queryset.annotate.return_value.order_by.return_value = "hits"

        result = search("vintage lamp")

        mock_query.assert_called_once_with(
            "vintage lamp", search_type="plain", config="english"
        )
        mock_item.objects.filter.assert_called_once_with(search_vector="query-object")
        queryset.annotate.assert_called_once_with(rank="rank-expr")
        queryset.annotate.return_value.order_by.assert_called_once_with("-rank")
        self.assertEqual(result, "hits")

    @patch("ebay.search.SearchRank")
    @patch("ebay.search.SearchQuery")
    @patch("ebay.search.Item")
    def test_strips_query_whitespace(self, mock_item, mock_query, mock_rank):
        queryset = MagicMock()
        mock_item.objects.filter.return_value = queryset
        queryset.annotate.return_value.order_by.return_value = "hits"

        search("  xbox  ")

        mock_query.assert_called_once_with("xbox", search_type="plain", config="english")

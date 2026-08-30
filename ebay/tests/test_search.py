import unittest
from unittest.mock import MagicMock, patch

from ebay.constants import FILTER_OPTIONS
from ebay.search import inFilterOptions, search


class TestInFilterOptions(unittest.TestCase):

    def test_exact_key_matches(self):
        self.assertTrue(inFilterOptions("Books"))
        self.assertTrue(inFilterOptions("Rings"))

    def test_title_case_normalizes_query(self):
        self.assertTrue(inFilterOptions("xbox games"))
        self.assertTrue(inFilterOptions("nintendo games"))

    def test_allcaps_keys_do_not_match_title_case(self):
        self.assertFalse(inFilterOptions("DVD"))
        self.assertFalse(inFilterOptions("TV SHOWS"))

    def test_unknown_query_is_false(self):
        self.assertFalse(inFilterOptions("not a real filter"))
        self.assertFalse(inFilterOptions(""))

    def test_hyphenated_key_does_not_match_title_case(self):
        self.assertIn("Blu-ray", FILTER_OPTIONS)
        self.assertFalse(inFilterOptions("blu-ray"))


class TestSearch(unittest.TestCase):

    def _vector_weights(self, mock_search_vector):
        return {
            call.args[0]: call.kwargs["weight"]
            for call in mock_search_vector.call_args_list
        }

    @patch("ebay.search.Item")
    @patch("ebay.search.SearchQuery")
    @patch("ebay.search.SearchVector")
    def test_filter_option_weights_category_highest(self, mock_vector, mock_query, mock_item):
        mock_vector.return_value = MagicMock()
        mock_item.objects.annotate.return_value.filter.return_value = "hits"

        result = search("Books")

        self.assertEqual(result, "hits")
        mock_query.assert_called_once_with("Books", search_type="plain")
        self.assertEqual(
            self._vector_weights(mock_vector),
            {"name": "B", "category": "A", "seller_description": "C"},
        )

    @patch("ebay.search.Item")
    @patch("ebay.search.SearchQuery")
    @patch("ebay.search.SearchVector")
    def test_free_text_weights_description_highest(self, mock_vector, mock_query, mock_item):
        mock_vector.return_value = MagicMock()
        mock_item.objects.annotate.return_value.filter.return_value = "hits"

        result = search("vintage lamp")

        self.assertEqual(result, "hits")
        mock_query.assert_called_once_with("vintage lamp", search_type="plain")
        self.assertEqual(
            self._vector_weights(mock_vector),
            {"name": "B", "category": "C", "seller_description": "A"},
        )

    @patch("ebay.search.Item")
    @patch("ebay.search.SearchQuery")
    @patch("ebay.search.SearchVector")
    def test_annotates_and_filters_with_search_query(self, mock_vector, mock_query, mock_item):
        search_vector = MagicMock()
        mock_vector.return_value = search_vector
        queryset = MagicMock()
        mock_item.objects.annotate.return_value = queryset
        queryset.filter.return_value = []
        mock_query.return_value = "query-object"

        search("nintendo")

        mock_item.objects.annotate.assert_called_once()
        queryset.filter.assert_called_once_with(search="query-object")

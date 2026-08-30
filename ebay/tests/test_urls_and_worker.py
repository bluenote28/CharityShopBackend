import unittest
from unittest.mock import patch

from ebay.urls.item_urls import CategoryWithSlashConverter
from ebay.worker import get_redis


class TestCategoryWithSlashConverter(unittest.TestCase):

    def setUp(self):
        self.converter = CategoryWithSlashConverter()

    def test_to_python_returns_string(self):
        self.assertEqual(self.converter.to_python("Books"), "Books")
        self.assertEqual(self.converter.to_python("Kitchen, Dining & Bar"), "Kitchen, Dining & Bar")

    def test_to_url_encodes_slash(self):
        self.assertEqual(self.converter.to_url("Arts/Crafts"), "Arts%2FCrafts")
        self.assertEqual(self.converter.to_url("Books"), "Books")


class TestGetRedis(unittest.TestCase):

    @patch("ebay.worker.redis.from_url")
    def test_uses_redis_url_env(self, mock_from_url):
        mock_from_url.return_value = "connection"

        with patch("ebay.worker.REDIS_URL", "rediss://example:6379"):
            result = get_redis()

        mock_from_url.assert_called_once_with("rediss://example:6379", ssl_cert_reqs=None)
        self.assertEqual(result, "connection")

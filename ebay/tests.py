from django.test import TestCase, Client
from .models import *
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .ebay_client import EbayClient
from unittest.mock import patch, Mock, MagicMock
from .load_data_to_db import DatabaseLoader, WORD_FILTER
import unittest

EBAY_CHARITY_URL = 'https://api.ebay.com/buy/browse/v1/item_summary/search?limit=200&offset=200&charity_ids=351044585'
EBAY_CHARITY_ID = '351044585'


class CharityTestCase(TestCase):
    def setUp(self):
        Charity.objects.create(id=1234, name="Test Charity", description="Test Description")
        self.client = Client()

    def test_charity(self):
        charity = Charity.objects.get(name="Test Charity")
        self.assertEqual(charity.name, "Test Charity")
        self.assertEqual(charity.description, "Test Description")

    def test_charity_view(self):
        response = self.client.get('/api/charity/getCharities/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Charity")

class ItemTestCase(TestCase):
    def setUp(self):
        self.charity = Charity.objects.create(id=1, name="Test Charity", description="Test Description")
        Item.objects.create(ebay_id="123456789", name="Test Item", img_url="http://test.com", web_url="http://test.com", price=10.00, charity=self.charity)
        self.client = Client()

    def test_item(self):
        item = Item.objects.get(name="Test Item")
        self.assertEqual(item.name, "Test Item")
        self.assertEqual(item.ebay_id, "123456789")
        self.assertEqual(item.img_url, "http://test.com")
        self.assertEqual(item.web_url, "http://test.com")
        self.assertEqual(item.price, 10.00)
        self.assertEqual(item.charity.name, "Test Charity")

    def test_item_view(self):
        response = self.client.get('/api/items/ebaycharityitems/123456789')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Item")

class TestTokenGeneration(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testtokenusername', password='testtokenpassword') 
        self.user.save()       
        self.client = APIClient()

    def test_token_generation(self):
        response = self.client.post('/api/users/login/', {'username': 'testtokenusername', 'password': 'testtokenpassword'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)
        self.assertIn('refresh', response.data)

class UserTestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username="bobsmith", password="password", first_name="bob", last_name="smith")
        self.admin_user.is_staff = True
        self.admin_user.save()
        self.client = Client()

    def test_user(self):
        user = User.objects.get(username="bobsmith")
        self.assertEqual(user.username, "bobsmith")
        self.assertEqual(user.password, self.admin_user.password)

    def test_get_users_unauthorized(self):
        response = self.client.get('/api/users/getUsers/')
        self.assertEqual(response.status_code, 401)

    def test_get_users_authorized(self):
        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        response = client.get('/api/users/getUsers/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "bobsmith")
        
class EbayClientTest(TestCase):

    def setUp(self):
        self.client = EbayClient(EBAY_CHARITY_ID)

    def test_ebay_client(self):
        self.assertEqual(self.client.charity_id, EBAY_CHARITY_ID)
        self.assertEqual(self.client.charity_url, EBAY_CHARITY_URL)

    @patch("ebay.ebay_client.EbayClient.getItems")
    def test_call_ebay(self, mock_get_items):
        mock_get_items.return_value = {
            "itemSummaries": ["item1"]
        }

        response = self.client.getItems()
        self.assertTrue(len(response["itemSummaries"]) > 0)
        
class TestDatabaseLoaderInit(unittest.TestCase):

    @patch('ebay.load_data_to_db.EbayClient')
    def test_initializes_with_charity_id(self, mock_client):
        
        loader = DatabaseLoader("charity_456")
        
        self.assertEqual(loader.charity_id, "charity_456")
        mock_client.assert_called_once_with("charity_456")

    @patch('ebay.load_data_to_db.EbayClient')
    def test_initializes_counters_to_zero(self, mock_client):
        
        loader = DatabaseLoader("charity_456")
        
        self.assertEqual(loader.items_processed, 0)
        self.assertEqual(loader.items_saved, 0)
        self.assertEqual(loader.items_skipped, 0)


class TestWordFilter(unittest.TestCase):
 
    def test_word_filter_contains_expected_words(self):    
        self.assertIn('playboy', WORD_FILTER)
        self.assertIn('sexy', WORD_FILTER)
        self.assertIn('sexual', WORD_FILTER)
        self.assertIn('sex', WORD_FILTER)

    def test_word_filter_is_set(self):
        
        self.assertIsInstance(WORD_FILTER, set)

class TestContainsInvalidWord(unittest.TestCase):

    @patch('ebay.load_data_to_db.EbayClient')
    def setUp(self, mock_client):
        
        self.loader = DatabaseLoader("test_charity_123")
        self.method = self.loader._DatabaseLoader__containsInvalidWord

    def test_returns_true_for_invalid_word_playboy(self):
        self.assertTrue(self.method("Playboy Magazine"))

    def test_returns_true_for_invalid_word_sexy(self):
        self.assertTrue(self.method("SEXY dress"))

    def test_returns_true_for_invalid_word_sexual(self):
        self.assertTrue(self.method("sexual content"))

    def test_returns_true_for_invalid_word_sex(self):
        self.assertTrue(self.method("sex education book"))

    def test_returns_false_for_valid_title(self):
        self.assertFalse(self.method("Vintage Book Collection"))
        self.assertFalse(self.method("Beautiful Dress"))
        self.assertFalse(self.method("Educational Material"))

    def test_case_insensitive_uppercase(self):
        self.assertTrue(self.method("PLAYBOY"))

    def test_case_insensitive_mixed(self):
        self.assertTrue(self.method("PlayBoy"))

    def test_case_insensitive_lowercase(self):
        self.assertTrue(self.method("playboy"))

    def test_partial_word_match(self):
        self.assertTrue(self.method("sexiest item"))

class TestProcessItem(unittest.TestCase):

    @patch('ebay.load_data_to_db.EbayClient')
    def setUp(self, mock_client):
        
        self.loader = DatabaseLoader("test_charity_123")
        self.method = self.loader._DatabaseLoader__process_item
        self.sample_item = self._create_sample_item()

    def _create_sample_item(self):
        return {
            "itemId": "item123",
            "title": "Vintage Book Collection",
            "price": {"value": "29.99"},
            "itemWebUrl": "https://ebay.com/item123",
            "categories": [
                {"categoryId": "1", "categoryName": "Books"},
                {"categoryId": "2", "categoryName": "Collectibles"}
            ],
            "itemLocation": {"city": "New York", "country": "US"},
            "seller": {"username": "seller123"},
            "condition": "Used",
            "shippingOptions": [
                {"shippingCost": {"value": "5.99"}}
            ],
            "thumbnailImages": [
                {"imageUrl": "https://example.com/image.jpg"}
            ],
            "additionalImages": [
                {"imageUrl": "https://example.com/image2.jpg"}
            ]
        }

    def test_processes_valid_item_correctly(self):
        result = self.method(self.sample_item)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "Vintage Book Collection")
        self.assertEqual(result["price"], "29.99")
        self.assertEqual(result["web_url"], "https://ebay.com/item123")
        self.assertEqual(result["charity"], "test_charity_123")
        self.assertEqual(result["category"], "Collectibles")
        self.assertEqual(result["ebay_id"], "item123")
        self.assertEqual(result["shipping_price"], "5.99")
        self.assertEqual(result["img_url"], "https://example.com/image.jpg")
        self.assertEqual(result["condition"], "Used")

    def test_returns_none_for_invalid_title(self):
        self.sample_item["title"] = "Playboy Magazine Collection"
        result = self.method(self.sample_item)  
        self.assertIsNone(result)

    def test_returns_none_for_adult_only(self):
        self.sample_item["adultOnly"] = True
        result = self.method(self.sample_item)
        self.assertIsNone(result)

    def test_handles_missing_shipping_options(self):
        del self.sample_item["shippingOptions"]
        result = self.method(self.sample_item)
        self.assertIsNotNone(result)
        self.assertIsNone(result["shipping_price"])

    def test_handles_empty_shipping_options(self):
        self.sample_item["shippingOptions"] = []
        result = self.method(self.sample_item)
        self.assertIsNotNone(result)
        self.assertIsNone(result["shipping_price"])

    def test_handles_missing_thumbnail_images(self):
        del self.sample_item["thumbnailImages"]
        result = self.method(self.sample_item)
        self.assertIsNotNone(result)
        self.assertIsNone(result["img_url"])

    def test_handles_missing_additional_images(self):
        del self.sample_item["additionalImages"]
        result = self.method(self.sample_item)
        self.assertIsNotNone(result)
        self.assertEqual(result["additional_images"], {"additionalImages": []})

    def test_handles_exception_gracefully(self):
        invalid_item = {"itemId": "bad_item"}
        result = self.method(invalid_item)     
        self.assertIsNone(result)

    def test_adult_only_defaults_to_false(self):
        self.assertNotIn("adultOnly", self.sample_item)
        result = self.method(self.sample_item)
        self.assertIsNotNone(result)

    def test_includes_category_list(self):
        result = self.method(self.sample_item)
        self.assertEqual(len(result["category_list"]), 2)

    def test_includes_seller_info(self):
        result = self.method(self.sample_item)
        self.assertEqual(result["seller"], {"username": "seller123"})

    def test_includes_item_location(self):
        result = self.method(self.sample_item)   
        self.assertEqual(result["item_location"], {"city": "New York", "country": "US"})

class TestGetExistingEbayIds(unittest.TestCase):

    @patch('ebay.load_data_to_db.EbayClient')
    def setUp(self, mock_client):
        
        self.loader = DatabaseLoader("test_charity_123")
        self.method = self.loader._DatabaseLoader__get_existing_ebay_ids

    @patch('ebay.models.Item')
    def test_returns_set_of_existing_ids(self, mock_item_model):
        mock_queryset = Mock()
        mock_queryset.values_list.return_value = ["id1", "id2"]
        mock_item_model.objects.filter.return_value = mock_queryset
        
        with patch('ebay.models.Item', mock_item_model):
            result = self.method(["id1", "id2", "id3"])
        
        self.assertIsInstance(result, set)
        self.assertEqual(result, {"id1", "id2"})

    @patch('ebay.models.Item')
    def test_returns_empty_set_when_no_existing(self, mock_item_model):
        mock_queryset = Mock()
        mock_queryset.values_list.return_value = []
        mock_item_model.objects.filter.return_value = mock_queryset
        
        with patch('ebay.models.Item', mock_item_model):
            result = self.method(["id1", "id2"])
        
        self.assertEqual(result, set())

    @patch('ebay.models.Item')
    def test_calls_filter_with_correct_ids(self, mock_item_model):
        mock_queryset = Mock()
        mock_queryset.values_list.return_value = []
        mock_item_model.objects.filter.return_value = mock_queryset
        
        test_ids = ["id1", "id2", "id3"]
        
        with patch('ebay.models.Item', mock_item_model):
            self.method(test_ids)
        
        mock_item_model.objects.filter.assert_called_once_with(ebay_id__in=test_ids)

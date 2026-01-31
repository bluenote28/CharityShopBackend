from django.test import TestCase, Client, RequestFactory
from .models import *
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .ebay_client import EbayClient
from unittest.mock import patch, Mock, MagicMock
from .load_data_to_db import DatabaseLoader, WORD_FILTER
import unittest
from ebay.views.item_views import EbayCharityItems


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
        self.charity = Charity.objects.create(
            id=1,
            name="Test Charity",
            description="Test Description"
        )
        self.item = Item.objects.create(
            ebay_id="123456789",
            name="Test Item",
            img_url="http://test.com",
            web_url="http://test.com",
            price=10.00,
            charity=self.charity
        )
        self.client = Client()
        self.factory = RequestFactory()
        self.view = EbayCharityItems.as_view()

    def test_item_model_fields(self):
        item = Item.objects.get(name="Test Item")
        self.assertEqual(item.name, "Test Item")
        self.assertEqual(item.ebay_id, "123456789")
        self.assertEqual(item.img_url, "http://test.com")
        self.assertEqual(item.web_url, "http://test.com")
        self.assertEqual(item.price, 10.00)
        self.assertEqual(item.charity.name, "Test Charity")

    @patch('ebay.views.item_views.retrieveItem')
    def test_get_item_by_id_found(self, mock_retrieve):
        mock_retrieve.return_value = self.item
        response = self.client.get('/api/items/ebaycharityitems/123456789')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Item")
        mock_retrieve.assert_called_once_with('123456789')

    @patch('ebay.views.item_views.retrieveItem')
    def test_get_item_by_id_not_found(self, mock_retrieve):
        mock_retrieve.return_value = None
        response = self.client.get('/api/items/ebaycharityitems/999999999')
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, "Item not found")

    def test_search_items_with_results(self):
        response = self.client.get('/api/items/ebaycharityitems/search/Test')
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)

    def test_search_items_no_results(self):
        response = self.client.get('/api/items/ebaycharityitems/search/NonExistentItem')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

    @patch('ebay.views.item_views.getItemsBySubCategory')
    def test_get_items_by_category_with_results(self, mock_get_category):
        mock_get_category.return_value = Item.objects.all()
        response = self.client.get('/api/items/ebaycharityitems/category/Electronics')
        
        self.assertEqual(response.status_code, 200)
        mock_get_category.assert_called_once_with('Electronics')
        self.assertIn('results', response.data)

    @patch('ebay.views.item_views.getItemsBySubCategory')
    def test_get_items_by_category_empty(self, mock_get_category):
        mock_get_category.return_value = Item.objects.none()
        response = self.client.get('/api/items/ebaycharityitems/category/EmptyCategory')
        
        self.assertEqual(response.status_code, 200)
        mock_get_category.assert_called_once_with('EmptyCategory')

    def test_no_parameters_returns_400(self):
        request = self.factory.get('/fake-url/')
        response = self.view(request)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            "Please provide an item_id, search_text, or category_id"
        )

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

class TestSaveItemsBatch(unittest.TestCase):

    @patch('ebay.load_data_to_db.EbayClient')
    def setUp(self, mock_client):    
        self.loader = DatabaseLoader("test_charity_123")
        self.method = self.loader._DatabaseLoader__save_items_batch

    @patch('ebay.load_data_to_db.transaction')
    @patch('ebay.serializers.ItemSerializer')
    def test_saves_valid_items(self, mock_serializer_class, mock_transaction):
        mock_serializer = Mock()
        mock_serializer.is_valid.return_value = True
        mock_serializer_class.return_value = mock_serializer
        
        items = [
            {"ebay_id": "id1", "name": "Item 1"},
            {"ebay_id": "id2", "name": "Item 2"}
        ]
        
        result = self.method(items)
        
        self.assertEqual(result, 2)
        self.assertEqual(mock_serializer.save.call_count, 2)

    @patch('ebay.load_data_to_db.transaction')
    @patch('ebay.serializers.ItemSerializer')
    def test_skips_invalid_items(self, mock_serializer_class, mock_transaction):
        """Should skip items that fail validation"""
        mock_serializer = Mock()
        mock_serializer.is_valid.side_effect = [True, False, True]
        mock_serializer.errors = {"name": ["Required field"]}
        mock_serializer_class.return_value = mock_serializer
        
        items = [
            {"ebay_id": "id1"},
            {"ebay_id": "id2"},
            {"ebay_id": "id3"}
        ]
        
        result = self.method(items)
        
        self.assertEqual(result, 2)
        self.assertEqual(mock_serializer.save.call_count, 2)

    @patch('ebay.load_data_to_db.transaction')
    @patch('ebay.serializers.ItemSerializer')
    def test_returns_zero_for_empty_list(self, mock_serializer_class, mock_transaction):
        result = self.method([])
        
        self.assertEqual(result, 0)
        mock_serializer_class.assert_not_called()

    @patch('ebay.load_data_to_db.transaction')
    @patch('ebay.serializers.ItemSerializer')
    def test_uses_atomic_transaction(self, mock_serializer_class, mock_transaction):
        mock_serializer = Mock()
        mock_serializer.is_valid.return_value = True
        mock_serializer_class.return_value = mock_serializer
        
        self.method([{"ebay_id": "id1"}])
        
        mock_transaction.atomic.assert_called_once()

class TestLoadItemsToDb(unittest.TestCase):

    @patch('ebay.load_data_to_db.EbayClient')
    def setUp(self, mock_client_class):
        
        self.mock_client = Mock()
        mock_client_class.return_value = self.mock_client
        self.loader = DatabaseLoader("test_charity_123")

    @patch('ebay.load_data_to_db.connection')
    def test_returns_success_no_items_when_no_item_summaries(self, mock_connection):
        self.mock_client.getItems.return_value = {"total": 0}
        result = self.loader.load_items_to_db()
        self.assertEqual(result, "success - no items")

    @patch('ebay.load_data_to_db.connection')
    def test_returns_error_message_on_api_error(self, mock_connection):
        self.mock_client.getItems.return_value = {"error": "API rate limit exceeded"}
        result = self.loader.load_items_to_db()
        self.assertEqual(result, "API rate limit exceeded")

    @patch('ebay.load_data_to_db.connection')
    @patch('ebay.load_data_to_db.DatabaseLoader._DatabaseLoader__save_items_batch')
    @patch('ebay.load_data_to_db.DatabaseLoader._DatabaseLoader__get_existing_ebay_ids')
    @patch('ebay.load_data_to_db.DatabaseLoader._DatabaseLoader__process_item')
    def test_processes_single_page_successfully(
        self, mock_process, mock_get_existing, mock_save, mock_connection
    ):
        self.mock_client.getItems.return_value = {
            "itemSummaries": [
                {"itemId": "id1", "title": "Item 1"},
                {"itemId": "id2", "title": "Item 2"}
            ]
        }
        mock_get_existing.return_value = set()
        mock_process.side_effect = [
            {"ebay_id": "id1", "name": "Item 1"},
            {"ebay_id": "id2", "name": "Item 2"}
        ]
        mock_save.return_value = 2
        
        result = self.loader.load_items_to_db()
        
        self.assertEqual(result, "success")
        self.assertEqual(self.loader.items_processed, 2)
        self.assertEqual(self.loader.items_saved, 2)
        self.assertEqual(self.loader.items_skipped, 0)

    @patch('ebay.load_data_to_db.connection')
    @patch('ebay.load_data_to_db.DatabaseLoader._DatabaseLoader__save_items_batch')
    @patch('ebay.load_data_to_db.DatabaseLoader._DatabaseLoader__get_existing_ebay_ids')
    @patch('ebay.load_data_to_db.DatabaseLoader._DatabaseLoader__process_item')
    def test_skips_existing_items(
        self, mock_process, mock_get_existing, mock_save, mock_connection
    ):
        self.mock_client.getItems.return_value = {
            "itemSummaries": [
                {"itemId": "id1", "title": "Item 1"},
                {"itemId": "id2", "title": "Item 2"}
            ]
        }
        mock_get_existing.return_value = {"id1"}
        mock_process.return_value = {"ebay_id": "id2", "name": "Item 2"}
        mock_save.return_value = 1
        
        result = self.loader.load_items_to_db()
        
        self.assertEqual(result, "success")
        self.assertEqual(self.loader.items_processed, 2)
        self.assertEqual(self.loader.items_skipped, 1)
        mock_process.assert_called_once()

    @patch('ebay.load_data_to_db.connection')
    @patch('ebay.load_data_to_db.DatabaseLoader._DatabaseLoader__save_items_batch')
    @patch('ebay.load_data_to_db.DatabaseLoader._DatabaseLoader__get_existing_ebay_ids')
    @patch('ebay.load_data_to_db.DatabaseLoader._DatabaseLoader__process_item')
    def test_skips_items_that_fail_processing(
        self, mock_process, mock_get_existing, mock_save, mock_connection
    ):
      
        self.mock_client.getItems.return_value = {
            "itemSummaries": [
                {"itemId": "id1", "title": "Playboy Magazine"},
                {"itemId": "id2", "title": "Valid Item"}
            ]
        }
        mock_get_existing.return_value = set()
        mock_process.side_effect = [None, {"ebay_id": "id2"}]
        mock_save.return_value = 1
        
        result = self.loader.load_items_to_db()
        
        self.assertEqual(result, "success")
        self.assertEqual(self.loader.items_skipped, 1)

    @patch('ebay.load_data_to_db.time.sleep')
    @patch('ebay.load_data_to_db.connection')
    @patch('ebay.load_data_to_db.DatabaseLoader._DatabaseLoader__save_items_batch')
    @patch('ebay.load_data_to_db.DatabaseLoader._DatabaseLoader__get_existing_ebay_ids')
    @patch('ebay.load_data_to_db.DatabaseLoader._DatabaseLoader__process_item')
    def test_handles_pagination(
        self, mock_process, mock_get_existing, mock_save,
        mock_connection, mock_sleep
    ):
        self.mock_client.getItems.side_effect = [
            {
                "itemSummaries": [{"itemId": "id1", "title": "Item 1"}],
                "next": "https://api.ebay.com/next_page"
            },
            {
                "itemSummaries": [{"itemId": "id2", "title": "Item 2"}]
            }
        ]
        mock_get_existing.return_value = set()
        mock_process.side_effect = [{"ebay_id": "id1"}, {"ebay_id": "id2"}]
        mock_save.return_value = 1
        
        result = self.loader.load_items_to_db()
        
        self.assertEqual(result, "success")
        self.assertEqual(self.loader.items_processed, 2)
        self.assertEqual(self.mock_client.getItems.call_count, 2)
        mock_sleep.assert_called_once_with(5)
        self.assertEqual(self.mock_client.charity_url, "https://api.ebay.com/next_page")

    @patch('ebay.load_data_to_db.connection')
    def test_closes_connection_on_exception(self, mock_connection):
        self.mock_client.getItems.side_effect = Exception("Network error")
        result = self.loader.load_items_to_db()
        self.assertIn("Network error", result)
        mock_connection.close.assert_called()

    @patch('ebay.load_data_to_db.connection')
    @patch('ebay.load_data_to_db.DatabaseLoader._DatabaseLoader__get_existing_ebay_ids')
    def test_handles_empty_page_gracefully(self, mock_get_existing, mock_connection):
        self.mock_client.getItems.return_value = {"itemSummaries": []}
        result = self.loader.load_items_to_db()
        self.assertEqual(result, "success")

    @patch('ebay.load_data_to_db.connection')
    @patch('ebay.load_data_to_db.DatabaseLoader._DatabaseLoader__save_items_batch')
    @patch('ebay.load_data_to_db.DatabaseLoader._DatabaseLoader__get_existing_ebay_ids')
    def test_does_not_save_when_no_items_to_save(
        self, mock_get_existing, mock_save, mock_connection
    ):
        self.mock_client.getItems.return_value = {
            "itemSummaries": [{"itemId": "id1", "title": "Item 1"}]
        }
        mock_get_existing.return_value = {"id1"}
        
        result = self.loader.load_items_to_db()
        
        self.assertEqual(result, "success")
        mock_save.assert_not_called()

    @patch('ebay.load_data_to_db.connection')
    def test_closes_connection_in_finally_block(self, mock_connection):
        self.mock_client.getItems.return_value = {"total": 0}
        self.loader.load_items_to_db()
        mock_connection.close.assert_called()


class TestIntegration(unittest.TestCase):

    def _create_sample_item(self, item_id="item123", title="Vintage Book"):
        return {
            "itemId": item_id,
            "title": title,
            "price": {"value": "29.99"},
            "itemWebUrl": f"https://ebay.com/{item_id}",
            "categories": [
                {"categoryId": "1", "categoryName": "Books"},
                {"categoryId": "2", "categoryName": "Collectibles"}
            ],
            "itemLocation": {"city": "New York", "country": "US"},
            "seller": {"username": "seller123"},
            "condition": "Used",
            "shippingOptions": [{"shippingCost": {"value": "5.99"}}],
            "thumbnailImages": [{"imageUrl": "https://example.com/image.jpg"}]
        }

    @patch('ebay.load_data_to_db.time.sleep')
    @patch('ebay.load_data_to_db.connection')
    @patch('ebay.load_data_to_db.transaction')
    @patch('ebay.serializers.ItemSerializer')
    @patch('ebay.models.Item')
    @patch('ebay.load_data_to_db.EbayClient')
    def test_full_flow_single_page(
        self, mock_client_class, mock_item_model, mock_serializer_class,
        mock_transaction, mock_connection, mock_sleep
    ):
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.getItems.return_value = {
            "itemSummaries": [self._create_sample_item()]
        }
        
        mock_queryset = Mock()
        mock_queryset.values_list.return_value = []
        mock_item_model.objects.filter.return_value = mock_queryset
        
        mock_serializer = Mock()
        mock_serializer.is_valid.return_value = True
        mock_serializer_class.return_value = mock_serializer
        
        loader = DatabaseLoader("test_charity")
        result = loader.load_items_to_db()
        
        self.assertEqual(result, "success")
        self.assertEqual(loader.items_processed, 1)
        self.assertEqual(loader.items_saved, 1)
        mock_serializer.save.assert_called_once()

    @patch('ebay.load_data_to_db.time.sleep')
    @patch('ebay.load_data_to_db.connection')
    @patch('ebay.load_data_to_db.transaction')
    @patch('ebay.serializers.ItemSerializer')
    @patch('ebay.models.Item')
    @patch('ebay.load_data_to_db.EbayClient')
    def test_filters_adult_and_invalid_content(
        self, mock_client_class, mock_item_model, mock_serializer_class,
        mock_transaction, mock_connection, mock_sleep
    ):
        
        adult_item = self._create_sample_item("adult1", "Normal Title")
        adult_item["adultOnly"] = True
        
        invalid_item = self._create_sample_item("invalid1", "Sexy Magazine")
        valid_item = self._create_sample_item("valid1", "Valid Book")
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.getItems.return_value = {
            "itemSummaries": [adult_item, invalid_item, valid_item]
        }
        
        mock_queryset = Mock()
        mock_queryset.values_list.return_value = []
        mock_item_model.objects.filter.return_value = mock_queryset
        
        mock_serializer = Mock()
        mock_serializer.is_valid.return_value = True
        mock_serializer_class.return_value = mock_serializer
        
        loader = DatabaseLoader("test_charity")
        result = loader.load_items_to_db()
        
        self.assertEqual(result, "success")
        self.assertEqual(loader.items_processed, 3)
        self.assertEqual(loader.items_skipped, 2)
        self.assertEqual(mock_serializer.save.call_count, 1)
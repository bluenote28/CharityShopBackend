from django.test import TestCase, Client, RequestFactory
from ..models import *
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from unittest.mock import patch
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
        
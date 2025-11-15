from django.test import TestCase, Client
from .models import *
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .ebay_client import EbayClient

EBAY_CHARITY_URL = 'https://api.ebay.com/buy/browse/v1/item_summary/search?limit=200&offset=200&charity_ids=351044585'
EBAY_CHARITY_ID = '351044585'


class CharityTestCase(TestCase):
    def setUp(self):
        Charity.objects.create(name="Test Charity", description="Test Description")
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
        response = self.client.get('/api/items/ebaycharityitems/')
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

    def test_call_ebay(self):
        response = self.client.getItems()
        self.assertEqual(response['total'] > 0, True)
        

        
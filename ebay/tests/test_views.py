import unittest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, RequestFactory
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework import status
from ..views.charity_views import EbayCharity
from ebay.models import Charity

class TestEbayCharityGet(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayCharity.as_view()

    @patch('ebay.views.charity_views.CharitySerializer')
    @patch('ebay.views.charity_views.Charity')
    def test_get_returns_all_charities(self, mock_charity_model, mock_serializer):
      
        mock_charities = [
            Mock(id=1, name="Charity 1"),
            Mock(id=2, name="Charity 2")
        ]
        mock_charity_model.objects.all.return_value = mock_charities
        
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = [
            {"id": 1, "name": "Charity 1"},
            {"id": 2, "name": "Charity 2"}
        ]
        mock_serializer.return_value = mock_serializer_instance
        
        request = self.factory.get('/api/charity/')
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        mock_charity_model.objects.all.assert_called_once()
        mock_serializer.assert_called_once_with(mock_charities, many=True)

    @patch('ebay.views.charity_views.CharitySerializer')
    @patch('ebay.views.charity_views.Charity')
    def test_get_returns_empty_list_when_no_charities(self, mock_charity_model, mock_serializer):
        mock_charity_model.objects.all.return_value = []
        
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = []
        mock_serializer.return_value = mock_serializer_instance
        
        request = self.factory.get('/api/charity/')
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    @patch('ebay.views.charity_views.CharitySerializer')
    @patch('ebay.views.charity_views.Charity')
    def test_get_returns_correct_serialized_data(self, mock_charity_model, mock_serializer):
        expected_data = [
            {
                "id": 1,
                "name": "Test Charity",
                "description": "Test Description",
                "donation_url": "http://test.com",
                "image_url": "http://test.com/image.png"
            }
        ]
        
        mock_charity_model.objects.all.return_value = [Mock()]
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = expected_data
        mock_serializer.return_value = mock_serializer_instance
        
        request = self.factory.get('/api/charity/')
        response = self.view(request)
        
        self.assertEqual(response.data, expected_data)


class TestEbayCharityPost(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayCharity.as_view()

    @patch('ebay.views.charity_views.addCharity')
    def test_post_success_returns_201(self, mock_add_charity):
        mock_add_charity.return_value = "Success"
        
        request_data = {
            "name": "New Charity",
            "description": "New Description",
            "donation_url": "http://newcharity.com",
            "image_url": "http://newcharity.com/image.png"
        }
        
        request = self.factory.post('/api/charity/', request_data, format='json')
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, "Sucesfully added charity")
        mock_add_charity.assert_called_once_with(request_data)

    @patch('ebay.views.charity_views.addCharity')
    def test_post_failure_returns_400(self, mock_add_charity):
        mock_add_charity.return_value = "Error"
        
        request_data = {
            "name": "New Charity"
        }
        
        request = self.factory.post('/api/charity/', request_data, format='json')
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "Failed to add charity")

    @patch('ebay.views.charity_views.addCharity')
    def test_post_with_empty_data(self, mock_add_charity):
        mock_add_charity.return_value = "Error"
        
        request = self.factory.post('/api/charity/', {}, format='json')
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('ebay.views.charity_views.addCharity')
    def test_post_calls_add_charity_with_correct_data(self, mock_add_charity):
        mock_add_charity.return_value = "Success"
        
        request_data = {
            "name": "Test Charity",
            "description": "Test Description",
            "donation_url": "http://test.com",
            "image_url": "http://test.com/image.png"
        }
        
        request = self.factory.post('/api/charity/', request_data, format='json')
        self.view(request)
        
        mock_add_charity.assert_called_once()
        call_args = mock_add_charity.call_args[0][0]
        self.assertEqual(call_args['name'], "Test Charity")
        self.assertEqual(call_args['description'], "Test Description")


class TestEbayCharityDelete(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayCharity.as_view()

    @patch('ebay.views.charity_views.deleteCharity')
    def test_delete_success_returns_204(self, mock_delete_charity):
        mock_delete_charity.return_value = "Success"
        
        request = self.factory.delete('/api/charity/1/')
        response = self.view(request, charity_id=1)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_delete_charity.assert_called_once_with(1)

    @patch('ebay.views.charity_views.deleteCharity')
    def test_delete_failure_returns_500(self, mock_delete_charity):
        mock_delete_charity.return_value = "Database error occurred"
        
        request = self.factory.delete('/api/charity/1/')
        response = self.view(request, charity_id=1)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, "Database error occurred")

    @patch('ebay.views.charity_views.deleteCharity')
    def test_delete_with_nonexistent_id(self, mock_delete_charity):
        mock_delete_charity.return_value = "Charity not found"
        
        request = self.factory.delete('/api/charity/999/')
        response = self.view(request, charity_id=999)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, "Charity not found")

    @patch('ebay.views.charity_views.deleteCharity')
    def test_delete_calls_delete_charity_with_correct_id(self, mock_delete_charity):
        mock_delete_charity.return_value = "Success"
        
        request = self.factory.delete('/api/charity/42/')
        self.view(request, charity_id=42)
        
        mock_delete_charity.assert_called_once_with(42)


class TestEbayCharityPut(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayCharity.as_view()

    @patch('ebay.views.charity_views.Charity')
    def test_put_success_returns_204(self, mock_charity_model):
        mock_charity = Mock()
        mock_charity_model.objects.get.return_value = mock_charity
        
        request_data = {
            "name": "Updated Charity",
            "description": "Updated Description",
            "donation_url": "http://updated.com",
            "image_url": "http://updated.com/image.png"
        }
        
        request = self.factory.put('/api/charity/1/', request_data, format='json')
        response = self.view(request, charity_id=1)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_charity.save.assert_called_once()

    @patch('ebay.views.charity_views.Charity')
    def test_put_updates_charity_fields(self, mock_charity_model):
        mock_charity = Mock()
        mock_charity_model.objects.get.return_value = mock_charity
        
        request_data = {
            "name": "Updated Name",
            "description": "Updated Description",
            "donation_url": "http://updated.com",
            "image_url": "http://updated.com/image.png"
        }
        
        request = self.factory.put('/api/charity/1/', request_data, format='json')
        self.view(request, charity_id=1)
        
        self.assertEqual(mock_charity.name, "Updated Name")
        self.assertEqual(mock_charity.description, "Updated Description")
        self.assertEqual(mock_charity.donation_url, "http://updated.com")
        self.assertEqual(mock_charity.image_url, "http://updated.com/image.png")

    @patch('ebay.views.charity_views.Charity')
    def test_put_charity_not_found_returns_500(self, mock_charity_model):
        mock_charity_model.objects.get.side_effect = Exception("Charity not found")
        
        request_data = {
            "name": "Updated Charity",
            "description": "Updated Description",
            "donation_url": "http://updated.com",
            "image_url": "http://updated.com/image.png"
        }
        
        request = self.factory.put('/api/charity/999/', request_data, format='json')
        response = self.view(request, charity_id=999)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('ebay.views.charity_views.Charity')
    def test_put_with_missing_fields_returns_500(self, mock_charity_model):
        mock_charity = Mock()
        mock_charity_model.objects.get.return_value = mock_charity
        
        request_data = {
            "name": "Updated Charity"
        }
        
        request = self.factory.put('/api/charity/1/', request_data, format='json')
        response = self.view(request, charity_id=1)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('ebay.views.charity_views.Charity')
    def test_put_save_failure_returns_500(self, mock_charity_model):
        mock_charity = Mock()
        mock_charity.save.side_effect = Exception("Database error")
        mock_charity_model.objects.get.return_value = mock_charity
        
        request_data = {
            "name": "Updated Charity",
            "description": "Updated Description",
            "donation_url": "http://updated.com",
            "image_url": "http://updated.com/image.png"
        }
        
        request = self.factory.put('/api/charity/1/', request_data, format='json')
        response = self.view(request, charity_id=1)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('ebay.views.charity_views.Charity')
    def test_put_calls_get_with_correct_id(self, mock_charity_model):
        mock_charity = Mock()
        mock_charity_model.objects.get.return_value = mock_charity
        
        request_data = {
            "name": "Updated Charity",
            "description": "Updated Description",
            "donation_url": "http://updated.com",
            "image_url": "http://updated.com/image.png"
        }
        
        request = self.factory.put('/api/charity/42/', request_data, format='json')
        self.view(request, charity_id=42)
        
        mock_charity_model.objects.get.assert_called_once_with(id=42)


class TestEbayCharityInit(unittest.TestCase):

    def test_init_creates_instance(self):
        view = EbayCharity()
        self.assertIsInstance(view, EbayCharity)


class TestEbayCharityIntegration(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayCharity.as_view()

    @patch('ebay.views.charity_views.addCharity')
    @patch('ebay.views.charity_views.deleteCharity')
    @patch('ebay.views.charity_views.Charity')
    @patch('ebay.views.charity_views.CharitySerializer')
    def test_full_crud_flow(self, mock_serializer, mock_charity_model, 
                           mock_delete, mock_add):
        mock_add.return_value = "Success"
        post_data = {
            "name": "Test Charity",
            "description": "Test",
            "donation_url": "http://test.com",
            "image_url": "http://test.com/img.png"
        }
        request = self.factory.post('/api/charity/', post_data, format='json')
        response = self.view(request)
        self.assertEqual(response.status_code, 201)

        mock_charity_model.objects.all.return_value = []
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = [post_data]
        mock_serializer.return_value = mock_serializer_instance
        
        request = self.factory.get('/api/charity/')
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

        mock_charity = Mock()
        mock_charity_model.objects.get.return_value = mock_charity
        
        put_data = {
            "name": "Updated Charity",
            "description": "Updated",
            "donation_url": "http://updated.com",
            "image_url": "http://updated.com/img.png"
        }
        request = self.factory.put('/api/charity/1/', put_data, format='json')
        response = self.view(request, charity_id=1)
        self.assertEqual(response.status_code, 204)

        mock_delete.return_value = "Success"
        request = self.factory.delete('/api/charity/1/')
        response = self.view(request, charity_id=1)
        self.assertEqual(response.status_code, 204)
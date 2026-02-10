import unittest
from unittest.mock import Mock, patch
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from ..views.charity_views import EbayCharity
from ebay.views.report_view import EbayReportView
from django.contrib.auth.models import User as DjangoUser
from django.db import IntegrityError
import smtplib
from ebay.views.user_views import (
    GetUserProfile,
    UpdateUserProfile,
    GetUsers,
    RegisterUser,
    MyTokenObtainPairSerializer,
    MyTokenObtainPairView
)

class TestEbayCharityGet(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayCharity.as_view()
        self.disk_patcher = patch('ebay.views.charity_views.disk')
        self.mock_disk = self.disk_patcher.start()
        self.mock_disk.get.return_value = None

    def tearDown(self):
        self.disk_patcher.stop()

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
        self.disk_patcher = patch('ebay.views.charity_views.disk')
        self.mock_disk = self.disk_patcher.start()

    def tearDown(self):
        self.disk_patcher.stop()

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
        self.disk_patcher = patch('ebay.views.charity_views.disk')
        self.mock_disk = self.disk_patcher.start()

    def tearDown(self):
        self.disk_patcher.stop()

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
        self.disk_patcher = patch('ebay.views.charity_views.disk')
        self.mock_disk = self.disk_patcher.start()

    def tearDown(self):
        self.disk_patcher.stop()

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
        with patch('ebay.views.charity_views.disk'):
            view = EbayCharity()
            self.assertIsInstance(view, EbayCharity)


class TestEbayCharityIntegration(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayCharity.as_view()
        self.disk_patcher = patch('ebay.views.charity_views.disk')
        self.mock_disk = self.disk_patcher.start()
        self.mock_disk.get.return_value = None

    def tearDown(self):
        self.disk_patcher.stop()

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


############################# Charity Cache Tests ##################################

class TestEbayCharityCaching(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayCharity.as_view()
        self.disk_patcher = patch('ebay.views.charity_views.disk')
        self.mock_disk = self.disk_patcher.start()

    def tearDown(self):
        self.disk_patcher.stop()

    def test_get_returns_cached_data_on_cache_hit(self):
        cached_data = [{"id": 1, "name": "Cached Charity"}]
        self.mock_disk.get.return_value = cached_data

        request = self.factory.get('/api/charity/')
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, cached_data)
        self.mock_disk.get.assert_called_once_with('charities_list')

    @patch('ebay.views.charity_views.CharitySerializer')
    @patch('ebay.views.charity_views.Charity')
    def test_get_queries_db_on_cache_miss(self, mock_charity_model, mock_serializer):
        self.mock_disk.get.return_value = None

        mock_charity_model.objects.all.return_value = [Mock()]
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = [{"id": 1}]
        mock_serializer.return_value = mock_serializer_instance

        request = self.factory.get('/api/charity/')
        self.view(request)

        mock_charity_model.objects.all.assert_called_once()

    @patch('ebay.views.charity_views.CharitySerializer')
    @patch('ebay.views.charity_views.Charity')
    def test_get_sets_cache_on_cache_miss(self, mock_charity_model, mock_serializer):
        self.mock_disk.get.return_value = None

        expected_data = [{"id": 1, "name": "Charity 1"}]
        mock_charity_model.objects.all.return_value = [Mock()]
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = expected_data
        mock_serializer.return_value = mock_serializer_instance

        request = self.factory.get('/api/charity/')
        self.view(request)

        self.mock_disk.set.assert_called_once_with('charities_list', expected_data, 60 * 60)

    def test_get_does_not_query_db_on_cache_hit(self):
        self.mock_disk.get.return_value = [{"id": 1}]

        with patch('ebay.views.charity_views.Charity') as mock_charity_model:
            request = self.factory.get('/api/charity/')
            self.view(request)
            mock_charity_model.objects.all.assert_not_called()

    @patch('ebay.views.charity_views.addCharity')
    def test_post_success_invalidates_charities_cache(self, mock_add_charity):
        mock_add_charity.return_value = "Success"

        request = self.factory.post('/api/charity/', {"name": "Test"}, format='json')
        self.view(request)

        self.mock_disk.delete.assert_any_call('charities_list')

    @patch('ebay.views.charity_views.addCharity')
    def test_post_failure_does_not_invalidate_cache(self, mock_add_charity):
        mock_add_charity.return_value = "Error"

        request = self.factory.post('/api/charity/', {}, format='json')
        self.view(request)

        self.mock_disk.delete.assert_not_called()

    @patch('ebay.views.charity_views.deleteCharity')
    def test_delete_success_invalidates_charities_cache(self, mock_delete_charity):
        mock_delete_charity.return_value = "Success"

        request = self.factory.delete('/api/charity/1/')
        self.view(request, charity_id=1)

        self.mock_disk.delete.assert_any_call('charities_list')

    @patch('ebay.views.charity_views.deleteCharity')
    def test_delete_failure_does_not_invalidate_cache(self, mock_delete_charity):
        mock_delete_charity.return_value = "Database error"

        request = self.factory.delete('/api/charity/1/')
        self.view(request, charity_id=1)

        self.mock_disk.delete.assert_not_called()

    @patch('ebay.views.charity_views.Charity')
    def test_put_success_invalidates_charities_cache(self, mock_charity_model):
        mock_charity = Mock()
        mock_charity_model.objects.get.return_value = mock_charity

        request_data = {
            "name": "Updated", "description": "Updated",
            "donation_url": "http://u.com", "image_url": "http://u.com/i.png"
        }
        request = self.factory.put('/api/charity/1/', request_data, format='json')
        self.view(request, charity_id=1)

        self.mock_disk.delete.assert_any_call('charities_list')

    @patch('ebay.views.charity_views.Charity')
    def test_put_failure_does_not_invalidate_cache(self, mock_charity_model):
        mock_charity_model.objects.get.side_effect = Exception("Not found")

        request_data = {
            "name": "Updated", "description": "Updated",
            "donation_url": "http://u.com", "image_url": "http://u.com/i.png"
        }
        request = self.factory.put('/api/charity/1/', request_data, format='json')
        self.view(request, charity_id=1)

        self.mock_disk.delete.assert_not_called()


############################# Report View Tests ##################################

class TestEbayReportViewGet(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayReportView.as_view()
        self.disk_patcher = patch('ebay.views.report_view.disk')
        self.mock_disk = self.disk_patcher.start()
        self.mock_disk.get.return_value = None

        self.mock_admin_user = Mock(spec=DjangoUser)
        self.mock_admin_user.id = 1
        self.mock_admin_user.username = "admin"
        self.mock_admin_user.is_staff = True
        self.mock_admin_user.is_authenticated = True

        self.mock_regular_user = Mock(spec=DjangoUser)
        self.mock_regular_user.id = 2
        self.mock_regular_user.username = "regular"
        self.mock_regular_user.is_staff = False
        self.mock_regular_user.is_authenticated = True

    def tearDown(self):
        self.disk_patcher.stop()

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_get_returns_report_data(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 10
        mock_charity_model.objects.count.return_value = 2

        mock_charity_1 = Mock()
        mock_charity_1.name = "Charity One"
        mock_charity_2 = Mock()
        mock_charity_2.name = "Charity Two"

        mock_charity_model.objects.all.return_value = [mock_charity_1, mock_charity_2]

        mock_item_model.objects.filter.return_value.count.side_effect = [5, 5]

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 10)
        self.assertEqual(response.data['total_charities'], 2)
        self.assertEqual(len(response.data['items_per_charity']), 2)

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_get_returns_correct_items_per_charity(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 15
        mock_charity_model.objects.count.return_value = 3

        mock_charity_1 = Mock()
        mock_charity_1.name = "Charity A"
        mock_charity_2 = Mock()
        mock_charity_2.name = "Charity B"
        mock_charity_3 = Mock()
        mock_charity_3.name = "Charity C"

        mock_charity_model.objects.all.return_value = [
            mock_charity_1,
            mock_charity_2,
            mock_charity_3
        ]

        mock_item_model.objects.filter.return_value.count.side_effect = [10, 3, 2]

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        items_per_charity = response.data['items_per_charity']
        self.assertEqual(items_per_charity[0]['name'], "Charity A")
        self.assertEqual(items_per_charity[0]['item_count'], 10)
        self.assertEqual(items_per_charity[1]['name'], "Charity B")
        self.assertEqual(items_per_charity[1]['item_count'], 3)
        self.assertEqual(items_per_charity[2]['name'], "Charity C")
        self.assertEqual(items_per_charity[2]['item_count'], 2)

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_get_returns_empty_data_when_no_items_or_charities(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 0
        mock_charity_model.objects.count.return_value = 0
        mock_charity_model.objects.all.return_value = []

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 0)
        self.assertEqual(response.data['total_charities'], 0)
        self.assertEqual(response.data['items_per_charity'], [])

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_get_returns_charity_with_zero_items(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 0
        mock_charity_model.objects.count.return_value = 1

        mock_charity = Mock()
        mock_charity.name = "Empty Charity"
        mock_charity_model.objects.all.return_value = [mock_charity]

        mock_item_model.objects.filter.return_value.count.return_value = 0

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items_per_charity'][0]['name'], "Empty Charity")
        self.assertEqual(response.data['items_per_charity'][0]['item_count'], 0)

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_get_calls_item_count(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 5
        mock_charity_model.objects.count.return_value = 1
        mock_charity_model.objects.all.return_value = []

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        self.view(request)

        mock_item_model.objects.count.assert_called_once()

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_get_calls_charity_count(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 5
        mock_charity_model.objects.count.return_value = 1
        mock_charity_model.objects.all.return_value = []

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        self.view(request)

        mock_charity_model.objects.count.assert_called_once()

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_get_calls_charity_all(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 5
        mock_charity_model.objects.count.return_value = 1
        mock_charity_model.objects.all.return_value = []

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        self.view(request)

        mock_charity_model.objects.all.assert_called_once()

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_get_filters_items_by_charity(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 10
        mock_charity_model.objects.count.return_value = 2

        mock_charity_1 = Mock()
        mock_charity_1.name = "Charity One"
        mock_charity_2 = Mock()
        mock_charity_2.name = "Charity Two"

        mock_charity_model.objects.all.return_value = [mock_charity_1, mock_charity_2]
        mock_item_model.objects.filter.return_value.count.return_value = 5

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        self.view(request)

        # Verify filter was called for each charity
        self.assertEqual(mock_item_model.objects.filter.call_count, 2)
        mock_item_model.objects.filter.assert_any_call(charity=mock_charity_1)
        mock_item_model.objects.filter.assert_any_call(charity=mock_charity_2)


class TestEbayReportViewPermissions(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayReportView.as_view()
        self.disk_patcher = patch('ebay.views.report_view.disk')
        self.mock_disk = self.disk_patcher.start()
        self.mock_disk.get.return_value = None

        self.mock_admin_user = Mock(spec=DjangoUser)
        self.mock_admin_user.id = 1
        self.mock_admin_user.username = "admin"
        self.mock_admin_user.is_staff = True
        self.mock_admin_user.is_authenticated = True

        self.mock_regular_user = Mock(spec=DjangoUser)
        self.mock_regular_user.id = 2
        self.mock_regular_user.username = "regular"
        self.mock_regular_user.is_staff = False
        self.mock_regular_user.is_authenticated = True

    def tearDown(self):
        self.disk_patcher.stop()

    def test_permission_denied_for_unauthenticated_user(self):
        request = self.factory.get('/api/report/')

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_permission_denied_for_non_admin_user(self):
        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_regular_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_permission_granted_for_admin_user(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 0
        mock_charity_model.objects.count.return_value = 0
        mock_charity_model.objects.all.return_value = []

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestEbayReportViewEdgeCases(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayReportView.as_view()
        self.disk_patcher = patch('ebay.views.report_view.disk')
        self.mock_disk = self.disk_patcher.start()
        self.mock_disk.get.return_value = None

        self.mock_admin_user = Mock(spec=DjangoUser)
        self.mock_admin_user.id = 1
        self.mock_admin_user.username = "admin"
        self.mock_admin_user.is_staff = True
        self.mock_admin_user.is_authenticated = True

    def tearDown(self):
        self.disk_patcher.stop()

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_get_with_large_number_of_charities(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 1000
        mock_charity_model.objects.count.return_value = 100

        mock_charities = []
        for i in range(100):
            mock_charity = Mock()
            mock_charity.name = f"Charity {i}"
            mock_charities.append(mock_charity)

        mock_charity_model.objects.all.return_value = mock_charities
        mock_item_model.objects.filter.return_value.count.return_value = 10

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items_per_charity']), 100)

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_get_with_charity_special_characters_in_name(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 5
        mock_charity_model.objects.count.return_value = 1

        mock_charity = Mock()
        mock_charity.name = "Charity's \"Special\" Name & More <test>"
        mock_charity_model.objects.all.return_value = [mock_charity]

        mock_item_model.objects.filter.return_value.count.return_value = 5

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['items_per_charity'][0]['name'],
            "Charity's \"Special\" Name & More <test>"
        )

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_get_response_structure(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 5
        mock_charity_model.objects.count.return_value = 1

        mock_charity = Mock()
        mock_charity.name = "Test Charity"
        mock_charity_model.objects.all.return_value = [mock_charity]

        mock_item_model.objects.filter.return_value.count.return_value = 5

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertIn('total_items', response.data)
        self.assertIn('total_charities', response.data)
        self.assertIn('items_per_charity', response.data)

        self.assertIsInstance(response.data['items_per_charity'], list)
        if len(response.data['items_per_charity']) > 0:
            self.assertIn('name', response.data['items_per_charity'][0])
            self.assertIn('item_count', response.data['items_per_charity'][0])

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_get_with_single_charity(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 25
        mock_charity_model.objects.count.return_value = 1

        mock_charity = Mock()
        mock_charity.name = "Only Charity"
        mock_charity_model.objects.all.return_value = [mock_charity]

        mock_item_model.objects.filter.return_value.count.return_value = 25

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 25)
        self.assertEqual(response.data['total_charities'], 1)
        self.assertEqual(len(response.data['items_per_charity']), 1)
        self.assertEqual(response.data['items_per_charity'][0]['item_count'], 25)


class TestEbayReportViewInit(unittest.TestCase):

    def test_init_creates_instance(self):
        with patch('ebay.views.report_view.disk'):
            view = EbayReportView()
            self.assertIsInstance(view, EbayReportView)

    def test_permission_classes_set(self):
        from rest_framework.permissions import IsAdminUser
        self.assertIn(IsAdminUser, EbayReportView.permission_classes)


class TestEbayReportViewIntegration(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayReportView.as_view()
        self.disk_patcher = patch('ebay.views.report_view.disk')
        self.mock_disk = self.disk_patcher.start()
        self.mock_disk.get.return_value = None

        self.mock_admin_user = Mock(spec=DjangoUser)
        self.mock_admin_user.id = 1
        self.mock_admin_user.username = "admin"
        self.mock_admin_user.is_staff = True
        self.mock_admin_user.is_authenticated = True

    def tearDown(self):
        self.disk_patcher.stop()

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_full_report_generation(self, mock_item_model, mock_charity_model):

        mock_item_model.objects.count.return_value = 50
        mock_charity_model.objects.count.return_value = 3

        mock_charity_1 = Mock()
        mock_charity_1.name = "Red Cross"
        mock_charity_2 = Mock()
        mock_charity_2.name = "UNICEF"
        mock_charity_3 = Mock()
        mock_charity_3.name = "WWF"

        mock_charity_model.objects.all.return_value = [
            mock_charity_1,
            mock_charity_2,
            mock_charity_3
        ]

        mock_item_model.objects.filter.return_value.count.side_effect = [20, 18, 12]

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 50)
        self.assertEqual(response.data['total_charities'], 3)

        items_per_charity = response.data['items_per_charity']
        self.assertEqual(len(items_per_charity), 3)

        charity_names = [entry['name'] for entry in items_per_charity]
        self.assertIn("Red Cross", charity_names)
        self.assertIn("UNICEF", charity_names)
        self.assertIn("WWF", charity_names)

        total_items_in_charities = sum(entry['item_count'] for entry in items_per_charity)
        self.assertEqual(total_items_in_charities, 50)


class TestEbayReportViewDataTypes(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayReportView.as_view()
        self.disk_patcher = patch('ebay.views.report_view.disk')
        self.mock_disk = self.disk_patcher.start()
        self.mock_disk.get.return_value = None

        self.mock_admin_user = Mock(spec=DjangoUser)
        self.mock_admin_user.id = 1
        self.mock_admin_user.username = "admin"
        self.mock_admin_user.is_staff = True
        self.mock_admin_user.is_authenticated = True

    def tearDown(self):
        self.disk_patcher.stop()

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_total_items_is_integer(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 10
        mock_charity_model.objects.count.return_value = 0
        mock_charity_model.objects.all.return_value = []

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertIsInstance(response.data['total_items'], int)

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_total_charities_is_integer(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 0
        mock_charity_model.objects.count.return_value = 5
        mock_charity_model.objects.all.return_value = []

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertIsInstance(response.data['total_charities'], int)

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_items_per_charity_is_list(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 0
        mock_charity_model.objects.count.return_value = 0
        mock_charity_model.objects.all.return_value = []

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertIsInstance(response.data['items_per_charity'], list)

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_charity_name_is_string(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 5
        mock_charity_model.objects.count.return_value = 1

        mock_charity = Mock()
        mock_charity.name = "Test Charity"
        mock_charity_model.objects.all.return_value = [mock_charity]

        mock_item_model.objects.filter.return_value.count.return_value = 5

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertIsInstance(response.data['items_per_charity'][0]['name'], str)

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_item_count_is_integer(self, mock_item_model, mock_charity_model):
        mock_item_model.objects.count.return_value = 5
        mock_charity_model.objects.count.return_value = 1

        mock_charity = Mock()
        mock_charity.name = "Test Charity"
        mock_charity_model.objects.all.return_value = [mock_charity]

        mock_item_model.objects.filter.return_value.count.return_value = 5

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertIsInstance(response.data['items_per_charity'][0]['item_count'], int)


############################# Report Cache Tests ##################################

class TestEbayReportCaching(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayReportView.as_view()
        self.disk_patcher = patch('ebay.views.report_view.disk')
        self.mock_disk = self.disk_patcher.start()

        self.mock_admin_user = Mock(spec=DjangoUser)
        self.mock_admin_user.id = 1
        self.mock_admin_user.username = "admin"
        self.mock_admin_user.is_staff = True
        self.mock_admin_user.is_authenticated = True

    def tearDown(self):
        self.disk_patcher.stop()

    def test_get_returns_cached_report_on_cache_hit(self):
        cached_report = {
            'total_items': 10,
            'total_charities': 2,
            'items_per_charity': [{"name": "Cached", "item_count": 10}]
        }
        self.mock_disk.get.return_value = cached_report

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, cached_report)
        self.mock_disk.get.assert_called_once_with('report_data')

    def test_get_does_not_query_db_on_cache_hit(self):
        self.mock_disk.get.return_value = {'total_items': 5, 'total_charities': 1, 'items_per_charity': []}

        with patch('ebay.views.report_view.Item') as mock_item, \
             patch('ebay.views.report_view.Charity') as mock_charity:
            request = self.factory.get('/api/report/')
            force_authenticate(request, user=self.mock_admin_user)

            self.view(request)

            mock_item.objects.count.assert_not_called()
            mock_charity.objects.count.assert_not_called()

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_get_sets_cache_on_cache_miss(self, mock_item_model, mock_charity_model):
        self.mock_disk.get.return_value = None

        mock_item_model.objects.count.return_value = 5
        mock_charity_model.objects.count.return_value = 1
        mock_charity = Mock()
        mock_charity.name = "Test"
        mock_charity_model.objects.all.return_value = [mock_charity]
        mock_item_model.objects.filter.return_value.count.return_value = 5

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        self.view(request)

        self.mock_disk.set.assert_called_once()
        call_args = self.mock_disk.set.call_args
        self.assertEqual(call_args[0][0], 'report_data')
        self.assertEqual(call_args[0][2], 60 * 30)

    @patch('ebay.views.report_view.Charity')
    @patch('ebay.views.report_view.Item')
    def test_get_caches_correct_data(self, mock_item_model, mock_charity_model):
        self.mock_disk.get.return_value = None

        mock_item_model.objects.count.return_value = 10
        mock_charity_model.objects.count.return_value = 1
        mock_charity = Mock()
        mock_charity.name = "Charity A"
        mock_charity_model.objects.all.return_value = [mock_charity]
        mock_item_model.objects.filter.return_value.count.return_value = 10

        request = self.factory.get('/api/report/')
        force_authenticate(request, user=self.mock_admin_user)

        self.view(request)

        cached_data = self.mock_disk.set.call_args[0][1]
        self.assertEqual(cached_data['total_items'], 10)
        self.assertEqual(cached_data['total_charities'], 1)
        self.assertEqual(cached_data['items_per_charity'][0]['name'], "Charity A")


########################## User View Tests #############################################################

class TestGetUserProfileGet(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = GetUserProfile.as_view()

        self.mock_user = Mock(spec=DjangoUser)
        self.mock_user.id = 1
        self.mock_user.username = "testuser@example.com"
        self.mock_user.email = "testuser@example.com"
        self.mock_user.first_name = "Test"
        self.mock_user.last_name = "User"
        self.mock_user.is_staff = False
        self.mock_user.is_authenticated = True

    @patch('ebay.views.user_views.UserSerializer')
    def test_get_returns_user_profile(self, mock_serializer):
        expected_data = {
            "id": 1,
            "username": "testuser@example.com",
            "email": "testuser@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = expected_data
        mock_serializer.return_value = mock_serializer_instance

        request = self.factory.get('/api/users/profile/')
        force_authenticate(request, user=self.mock_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)
        mock_serializer.assert_called_once_with(self.mock_user)

    def test_get_unauthenticated_returns_error(self):
        request = self.factory.get('/api/users/profile/')

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    @patch('ebay.views.user_views.UserSerializer')
    def test_get_returns_correct_user_data(self, mock_serializer):
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = {"id": 1, "username": "testuser@example.com"}
        mock_serializer.return_value = mock_serializer_instance

        request = self.factory.get('/api/users/profile/')
        force_authenticate(request, user=self.mock_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_serializer.assert_called_with(self.mock_user)


class TestGetUserProfilePut(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = GetUserProfile.as_view()

        self.mock_user = Mock(spec=DjangoUser)
        self.mock_user.id = 1
        self.mock_user.username = "testuser@example.com"
        self.mock_user.email = "testuser@example.com"
        self.mock_user.first_name = "Test"
        self.mock_user.last_name = "User"
        self.mock_user.is_staff = False
        self.mock_user.is_authenticated = True

    @patch('ebay.views.user_views.UserSerializerWithToken')
    @patch('ebay.views.user_views.make_password')
    def test_put_updates_user_profile(self, mock_make_password, mock_serializer):
        mock_make_password.return_value = "hashed_password"

        expected_data = {
            "id": 1,
            "username": "updated@example.com",
            "email": "updated@example.com",
            "first_name": "Updated",
            "last_name": "Name",
            "token": "test_token"
        }
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = expected_data
        mock_serializer.return_value = mock_serializer_instance

        request_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
            "password": "newpassword123"
        }

        request = self.factory.put('/api/users/profile/', request_data, format='json')
        force_authenticate(request, user=self.mock_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.mock_user.first_name, "Updated")
        self.assertEqual(self.mock_user.last_name, "Name")
        self.assertEqual(self.mock_user.email, "updated@example.com")
        self.mock_user.save.assert_called_once()

    @patch('ebay.views.user_views.UserSerializerWithToken')
    @patch('ebay.views.user_views.make_password')
    def test_put_updates_password_when_provided(self, mock_make_password, mock_serializer):
        mock_make_password.return_value = "hashed_new_password"

        mock_serializer_instance = Mock()
        mock_serializer_instance.data = {}
        mock_serializer.return_value = mock_serializer_instance

        test_password = "newpassword123"
        request_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password": test_password
        }

        request = self.factory.put('/api/users/profile/', request_data, format='json')
        force_authenticate(request, user=self.mock_user)

        self.view(request)

        mock_make_password.assert_called_once_with(test_password)
        self.assertEqual(self.mock_user.password, "hashed_new_password")

    @patch('ebay.views.user_views.UserSerializerWithToken')
    @patch('ebay.views.user_views.make_password')
    def test_put_does_not_update_password_when_empty(self, mock_make_password, mock_serializer):
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = {}
        mock_serializer.return_value = mock_serializer_instance

        request_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password": ""
        }

        request = self.factory.put('/api/users/profile/', request_data, format='json')
        force_authenticate(request, user=self.mock_user)

        self.view(request)

        mock_make_password.assert_not_called()

    def test_put_unauthenticated_returns_error(self):
        request_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password": ""
        }

        request = self.factory.put('/api/users/profile/', request_data, format='json')

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class TestUpdateUserProfile(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = UpdateUserProfile.as_view()

        self.mock_user = Mock(spec=DjangoUser)
        self.mock_user.id = 1
        self.mock_user.username = "testuser@example.com"
        self.mock_user.email = "testuser@example.com"
        self.mock_user.first_name = "Test"
        self.mock_user.last_name = "User"
        self.mock_user.is_staff = False
        self.mock_user.is_authenticated = True

    @patch('ebay.views.user_views.UserSerializerWithToken')
    @patch('ebay.views.user_views.make_password')
    def test_put_updates_user_profile(self, mock_make_password, mock_serializer):
        mock_make_password.return_value = "hashed_password"

        expected_data = {
            "id": 1,
            "username": "updated@example.com",
            "first_name": "Updated",
            "last_name": "Name"
        }
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = expected_data
        mock_serializer.return_value = mock_serializer_instance

        request_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
            "password": "newpassword123"
        }

        request = self.factory.put('/api/users/profile/update/', request_data, format='json')
        force_authenticate(request, user=self.mock_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.mock_user.first_name, "Updated")
        self.assertEqual(self.mock_user.last_name, "Name")
        self.mock_user.save.assert_called_once()

    @patch('ebay.views.user_views.UserSerializerWithToken')
    def test_put_without_password_change(self, mock_serializer):
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = {}
        mock_serializer.return_value = mock_serializer_instance

        request_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
            "password": ""
        }

        request = self.factory.put('/api/users/profile/update/', request_data, format='json')
        force_authenticate(request, user=self.mock_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_unauthenticated_returns_error(self):
        request_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password": ""
        }

        request = self.factory.put('/api/users/profile/update/', request_data, format='json')

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class TestGetUsers(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = GetUsers.as_view()

        self.mock_admin_user = Mock(spec=DjangoUser)
        self.mock_admin_user.id = 1
        self.mock_admin_user.username = "admin"
        self.mock_admin_user.is_staff = True
        self.mock_admin_user.is_authenticated = True

        self.mock_regular_user = Mock(spec=DjangoUser)
        self.mock_regular_user.id = 2
        self.mock_regular_user.username = "regular"
        self.mock_regular_user.is_staff = False
        self.mock_regular_user.is_authenticated = True

    @patch('ebay.views.user_views.UserSerializer')
    @patch('ebay.views.user_views.User')
    def test_get_returns_all_users(self, mock_user_model, mock_serializer):
        mock_users = [Mock(), Mock(), Mock()]
        mock_user_model.objects.all.return_value = mock_users

        expected_data = [
            {"id": 1, "username": "user1"},
            {"id": 2, "username": "user2"},
            {"id": 3, "username": "user3"}
        ]
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = expected_data
        mock_serializer.return_value = mock_serializer_instance

        request = self.factory.get('/api/users/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        mock_user_model.objects.all.assert_called_once()
        mock_serializer.assert_called_once_with(mock_users, many=True)

    @patch('ebay.views.user_views.UserSerializer')
    @patch('ebay.views.user_views.User')
    def test_get_returns_empty_list_when_no_users(self, mock_user_model, mock_serializer):
        mock_user_model.objects.all.return_value = []

        mock_serializer_instance = Mock()
        mock_serializer_instance.data = []
        mock_serializer.return_value = mock_serializer_instance

        request = self.factory.get('/api/users/')
        force_authenticate(request, user=self.mock_admin_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_get_permission_denied_for_non_admin(self):
        request = self.factory.get('/api/users/')
        force_authenticate(request, user=self.mock_regular_user)

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_permission_denied_for_unauthenticated(self):
        request = self.factory.get('/api/users/')

        response = self.view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class TestRegisterUser(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = RegisterUser.as_view()

    @patch('ebay.views.user_views.UserSerializerWithToken')
    @patch('ebay.views.user_views.FavoriteList')
    @patch('ebay.views.user_views.User')
    def test_post_creates_user_successfully(self, mock_user_model, mock_favorite_list, mock_serializer):
        mock_user = Mock()
        mock_user.id = 1
        mock_user_model.objects.create_user.return_value = mock_user

        mock_fav_list = Mock()
        mock_favorite_list.objects.create.return_value = mock_fav_list

        expected_data = {
            "id": 1,
            "username": "newuser@example.com",
            "token": "test_token"
        }
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = expected_data
        mock_serializer.return_value = mock_serializer_instance

        request_data = {
            "email": "newuser@example.com",
            "password": "testpassword123",
            "first_name": "New",
            "last_name": "User"
        }

        request = self.factory.post('/api/users/register/', request_data, format='json')

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_user_model.objects.create_user.assert_called_once_with(
            username="newuser@example.com",
            email="newuser@example.com",
            password="testpassword123",
            first_name="New",
            last_name="User"
        )

    @patch('ebay.views.user_views.FavoriteList')
    @patch('ebay.views.user_views.User')
    def test_post_creates_favorite_list_for_user(self, mock_user_model, mock_favorite_list):
        mock_user = Mock()
        mock_user.id = 1
        mock_user_model.objects.create_user.return_value = mock_user

        mock_fav_list = Mock()
        mock_favorite_list.objects.create.return_value = mock_fav_list

        request_data = {
            "email": "newuser@example.com",
            "password": "testpassword123",
            "first_name": "New",
            "last_name": "User"
        }

        request = self.factory.post('/api/users/register/', request_data, format='json')

        with patch('ebay.views.user_views.UserSerializerWithToken') as mock_serializer:
            mock_serializer_instance = Mock()
            mock_serializer_instance.data = {}
            mock_serializer.return_value = mock_serializer_instance

            self.view(request)

        mock_favorite_list.objects.create.assert_called_once_with(user_id=1)
        mock_fav_list.items.clear.assert_called_once()
        mock_fav_list.charities.clear.assert_called_once()
        mock_fav_list.save.assert_called_once()

    @patch('ebay.views.user_views.User')
    def test_post_user_already_exists_returns_error(self, mock_user_model):
        mock_user_model.objects.create_user.side_effect = IntegrityError()

        request_data = {
            "email": "existing@example.com",
            "password": "testpassword123",
            "first_name": "Existing",
            "last_name": "User"
        }

        request = self.factory.post('/api/users/register/', request_data, format='json')

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'User already exists')

    @patch('ebay.views.user_views.User')
    def test_post_generic_exception_returns_error(self, mock_user_model):
        mock_user_model.objects.create_user.side_effect = Exception("Database error")

        request_data = {
            "email": "newuser@example.com",
            "password": "testpassword123",
            "first_name": "New",
            "last_name": "User"
        }

        request = self.factory.post('/api/users/register/', request_data, format='json')

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('ebay.views.user_views.UserSerializerWithToken')
    @patch('ebay.views.user_views.FavoriteList')
    @patch('ebay.views.user_views.User')
    def test_post_returns_serialized_user_with_token(self, mock_user_model, mock_favorite_list, mock_serializer):
        mock_user = Mock()
        mock_user.id = 1
        mock_user_model.objects.create_user.return_value = mock_user

        mock_fav_list = Mock()
        mock_favorite_list.objects.create.return_value = mock_fav_list

        expected_data = {
            "id": 1,
            "username": "newuser@example.com",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "token": "jwt_token_here"
        }
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = expected_data
        mock_serializer.return_value = mock_serializer_instance

        request_data = {
            "email": "newuser@example.com",
            "password": "testpassword123",
            "first_name": "New",
            "last_name": "User"
        }

        request = self.factory.post('/api/users/register/', request_data, format='json')

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        mock_serializer.assert_called_once_with(mock_user, many=False)


class TestRegisterUserCreateFavoriteList(unittest.TestCase):

    @patch('ebay.views.user_views.FavoriteList')
    def test_create_favorite_list_creates_and_clears(self, mock_favorite_list):
        mock_fav_list = Mock()
        mock_favorite_list.objects.create.return_value = mock_fav_list

        view = RegisterUser()
        view.createFavoriteList(user_id=1)

        mock_favorite_list.objects.create.assert_called_once_with(user_id=1)
        mock_fav_list.items.clear.assert_called_once()
        mock_fav_list.charities.clear.assert_called_once()
        mock_fav_list.save.assert_called_once()

    @patch('ebay.views.user_views.FavoriteList')
    def test_create_favorite_list_with_different_user_ids(self, mock_favorite_list):
        mock_fav_list = Mock()
        mock_favorite_list.objects.create.return_value = mock_fav_list

        view = RegisterUser()

        for user_id in [1, 2, 100, 999]:
            mock_favorite_list.reset_mock()
            mock_fav_list.reset_mock()

            view.createFavoriteList(user_id=user_id)

            mock_favorite_list.objects.create.assert_called_once_with(user_id=user_id)


class TestMyTokenObtainPairSerializer(unittest.TestCase):

    def test_serializer_class_inherits_from_token_obtain_pair(self):
        from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
        self.assertTrue(issubclass(MyTokenObtainPairSerializer, TokenObtainPairSerializer))


class TestMyTokenObtainPairView(unittest.TestCase):

    def test_serializer_class_is_custom(self):
        self.assertEqual(MyTokenObtainPairView.serializer_class, MyTokenObtainPairSerializer)

    def test_view_inherits_from_token_obtain_pair_view(self):
        from rest_framework_simplejwt.views import TokenObtainPairView
        self.assertTrue(issubclass(MyTokenObtainPairView, TokenObtainPairView))


class TestGetUserProfilePermissions(unittest.TestCase):

    def test_permission_classes_include_is_authenticated(self):
        from rest_framework.permissions import IsAuthenticated
        self.assertIn(IsAuthenticated, GetUserProfile.permission_classes)


class TestUpdateUserProfilePermissions(unittest.TestCase):

    def test_permission_classes_include_is_authenticated(self):
        from rest_framework.permissions import IsAuthenticated
        self.assertIn(IsAuthenticated, UpdateUserProfile.permission_classes)


class TestGetUsersPermissions(unittest.TestCase):

    def test_permission_classes_include_is_admin_user(self):
        from rest_framework.permissions import IsAdminUser
        self.assertIn(IsAdminUser, GetUsers.permission_classes)


class TestUserViewsIntegration(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

        self.mock_admin_user = Mock(spec=DjangoUser)
        self.mock_admin_user.id = 1
        self.mock_admin_user.username = "admin"
        self.mock_admin_user.is_staff = True
        self.mock_admin_user.is_authenticated = True

        self.mock_regular_user = Mock(spec=DjangoUser)
        self.mock_regular_user.id = 2
        self.mock_regular_user.username = "regular@example.com"
        self.mock_regular_user.email = "regular@example.com"
        self.mock_regular_user.first_name = "Regular"
        self.mock_regular_user.last_name = "User"
        self.mock_regular_user.is_staff = False
        self.mock_regular_user.is_authenticated = True

    @patch('ebay.views.user_views.UserSerializer')
    def test_get_profile_flow(self, mock_serializer):
        view = GetUserProfile.as_view()

        expected_data = {
            "id": 2,
            "username": "regular@example.com",
            "email": "regular@example.com",
            "first_name": "Regular",
            "last_name": "User"
        }
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = expected_data
        mock_serializer.return_value = mock_serializer_instance

        request = self.factory.get('/api/users/profile/')
        force_authenticate(request, user=self.mock_regular_user)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], "regular@example.com")

    @patch('ebay.views.user_views.UserSerializerWithToken')
    @patch('ebay.views.user_views.FavoriteList')
    @patch('ebay.views.user_views.User')
    def test_register_user_flow(self, mock_user_model, mock_favorite_list, mock_serializer):
        register_view = RegisterUser.as_view()

        mock_user = Mock()
        mock_user.id = 3
        mock_user_model.objects.create_user.return_value = mock_user

        mock_fav_list = Mock()
        mock_favorite_list.objects.create.return_value = mock_fav_list

        mock_serializer_instance = Mock()
        mock_serializer_instance.data = {"id": 3, "username": "newuser@example.com", "token": "token"}
        mock_serializer.return_value = mock_serializer_instance

        register_data = {
            "email": "newuser@example.com",
            "password": "testpassword123",
            "first_name": "New",
            "last_name": "User"
        }

        request = self.factory.post('/api/users/register/', register_data, format='json')
        response = register_view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)


class TestUserViewsEdgeCases(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

        self.mock_user = Mock(spec=DjangoUser)
        self.mock_user.id = 1
        self.mock_user.username = "testuser@example.com"
        self.mock_user.is_staff = False
        self.mock_user.is_authenticated = True

    @patch('ebay.views.user_views.UserSerializerWithToken')
    @patch('ebay.views.user_views.make_password')
    def test_put_profile_with_special_characters_in_name(self, mock_make_password, mock_serializer):
        view = GetUserProfile.as_view()

        mock_serializer_instance = Mock()
        mock_serializer_instance.data = {}
        mock_serializer.return_value = mock_serializer_instance

        request_data = {
            "first_name": "Jose",
            "last_name": "O'Brien-Smith",
            "email": "jose@example.com",
            "password": ""
        }

        request = self.factory.put('/api/users/profile/', request_data, format='json')
        force_authenticate(request, user=self.mock_user)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.mock_user.first_name, "Jose")
        self.assertEqual(self.mock_user.last_name, "O'Brien-Smith")

    @patch('ebay.views.user_views.UserSerializerWithToken')
    @patch('ebay.views.user_views.make_password')
    def test_put_profile_updates_username_to_email(self, mock_make_password, mock_serializer):
        view = GetUserProfile.as_view()

        mock_serializer_instance = Mock()
        mock_serializer_instance.data = {}
        mock_serializer.return_value = mock_serializer_instance

        request_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "newemail@example.com",
            "password": ""
        }

        request = self.factory.put('/api/users/profile/', request_data, format='json')
        force_authenticate(request, user=self.mock_user)

        view(request)

        self.assertEqual(self.mock_user.username, "newemail@example.com")
        self.assertEqual(self.mock_user.email, "newemail@example.com")

    @patch('ebay.views.user_views.UserSerializerWithToken')
    @patch('ebay.views.user_views.make_password')
    def test_put_profile_with_long_password(self, mock_make_password, mock_serializer):
        view = GetUserProfile.as_view()

        mock_make_password.return_value = "hashed_long_password"
        mock_serializer_instance = Mock()
        mock_serializer_instance.data = {}
        mock_serializer.return_value = mock_serializer_instance

        long_password = "a" * 128
        request_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password": long_password
        }

        request = self.factory.put('/api/users/profile/', request_data, format='json')
        force_authenticate(request, user=self.mock_user)

        view(request)

        mock_make_password.assert_called_once_with(long_password)

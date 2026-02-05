import unittest
from unittest.mock import Mock, patch
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from ..views.charity_views import EbayCharity
from ebay.views.report_view import EbayReportView
from django.contrib.auth.models import User as DjangoUser

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


############################# Report View Tests ##################################

class TestEbayReportViewGet(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayReportView.as_view()
        
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
        
        self.mock_admin_user = Mock(spec=DjangoUser)
        self.mock_admin_user.id = 1
        self.mock_admin_user.username = "admin"
        self.mock_admin_user.is_staff = True
        self.mock_admin_user.is_authenticated = True

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
        view = EbayReportView()
        self.assertIsInstance(view, EbayReportView)

    def test_permission_classes_set(self):
        from rest_framework.permissions import IsAdminUser
        self.assertIn(IsAdminUser, EbayReportView.permission_classes)


class TestEbayReportViewIntegration(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EbayReportView.as_view()
        
        self.mock_admin_user = Mock(spec=DjangoUser)
        self.mock_admin_user.id = 1
        self.mock_admin_user.username = "admin"
        self.mock_admin_user.is_staff = True
        self.mock_admin_user.is_authenticated = True

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
        
        self.mock_admin_user = Mock(spec=DjangoUser)
        self.mock_admin_user.id = 1
        self.mock_admin_user.username = "admin"
        self.mock_admin_user.is_staff = True
        self.mock_admin_user.is_authenticated = True

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
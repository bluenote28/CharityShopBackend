import unittest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from checkout.views.session_views import (
    InitiateCheckoutView,
    CheckoutSessionDetailView,
    UpdateQuantityView,
    UpdateShippingOptionView,
    ApplyCouponView,
)
from checkout.models import CheckoutSession


class TestInitiateCheckoutView(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = InitiateCheckoutView.as_view()
        self.valid_payload = {
            "buyer_email": "test@example.com",
            "item_id": "v1|123456|0",
            "quantity": 1,
            "recipient_first_name": "John",
            "recipient_last_name": "Doe",
            "address_line1": "123 Main St",
            "city": "Springfield",
            "state_or_province": "IL",
            "postal_code": "62701",
            "country": "US",
        }

    @patch('checkout.views.session_views.CheckoutClient')
    def test_initiate_success_returns_201(self, mock_client_cls):
        mock_client = Mock()
        mock_client.initiate_checkout.return_value = {
            "checkoutSessionId": "session123",
            "pricingSummary": {
                "priceSubtotal": {"value": "29.99", "currency": "USD"},
                "deliveryCost": {"value": "5.99", "currency": "USD"},
                "tax": {"value": "2.40", "currency": "USD"},
                "total": {"value": "38.38", "currency": "USD"},
            }
        }
        mock_client_cls.return_value = mock_client

        request = self.factory.post('/api/checkout/initiate/', self.valid_payload, format='json')
        response = self.view(request)

        self.assertEqual(response.status_code, 201)

    @patch('checkout.views.session_views.CheckoutClient')
    def test_initiate_creates_local_checkout_session(self, mock_client_cls):
        mock_client = Mock()
        mock_client.initiate_checkout.return_value = {
            "checkoutSessionId": "session456",
            "pricingSummary": {
                "total": {"value": "38.38", "currency": "USD"},
            }
        }
        mock_client_cls.return_value = mock_client

        request = self.factory.post('/api/checkout/initiate/', self.valid_payload, format='json')
        self.view(request)

        self.assertTrue(CheckoutSession.objects.filter(ebay_session_id="session456").exists())

    def test_initiate_with_invalid_email_returns_400(self):
        payload = self.valid_payload.copy()
        payload['buyer_email'] = 'not-an-email'

        request = self.factory.post('/api/checkout/initiate/', payload, format='json')
        response = self.view(request)

        self.assertEqual(response.status_code, 400)

    def test_initiate_with_missing_required_fields_returns_400(self):
        request = self.factory.post('/api/checkout/initiate/', {"buyer_email": "test@test.com"}, format='json')
        response = self.view(request)

        self.assertEqual(response.status_code, 400)

    @patch('checkout.views.session_views.CheckoutClient')
    def test_initiate_ebay_error_returns_502(self, mock_client_cls):
        mock_client = Mock()
        mock_client.initiate_checkout.return_value = {"error": "eBay API error"}
        mock_client_cls.return_value = mock_client

        request = self.factory.post('/api/checkout/initiate/', self.valid_payload, format='json')
        response = self.view(request)

        self.assertEqual(response.status_code, 502)


class TestCheckoutSessionDetailView(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = CheckoutSessionDetailView.as_view()

    @patch('checkout.views.session_views.CheckoutClient')
    def test_get_session_returns_ebay_data(self, mock_client_cls):
        mock_client = Mock()
        expected = {"checkoutSessionId": "session123", "status": "ACTIVE"}
        mock_client.get_checkout_session.return_value = expected
        mock_client_cls.return_value = mock_client

        request = self.factory.get('/api/checkout/session123/')
        response = self.view(request, session_id='session123')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected)

    @patch('checkout.views.session_views.CheckoutClient')
    def test_get_session_updates_local_record(self, mock_client_cls):
        CheckoutSession.objects.create(
            ebay_session_id="session789",
            buyer_email="test@test.com",
            shipping_address={"city": "Test"},
            total=10.00
        )

        mock_client = Mock()
        mock_client.get_checkout_session.return_value = {
            "checkoutSessionId": "session789",
            "pricingSummary": {
                "total": {"value": "20.00", "currency": "USD"},
            }
        }
        mock_client_cls.return_value = mock_client

        request = self.factory.get('/api/checkout/session789/')
        self.view(request, session_id='session789')

        session = CheckoutSession.objects.get(ebay_session_id="session789")
        self.assertEqual(float(session.total), 20.00)

    @patch('checkout.views.session_views.CheckoutClient')
    def test_get_session_ebay_error_returns_502(self, mock_client_cls):
        mock_client = Mock()
        mock_client.get_checkout_session.return_value = {"error": "Not found"}
        mock_client_cls.return_value = mock_client

        request = self.factory.get('/api/checkout/session123/')
        response = self.view(request, session_id='session123')

        self.assertEqual(response.status_code, 502)

    @patch('checkout.views.session_views.CheckoutClient')
    def test_get_session_works_without_local_record(self, mock_client_cls):
        mock_client = Mock()
        mock_client.get_checkout_session.return_value = {"checkoutSessionId": "unknown"}
        mock_client_cls.return_value = mock_client

        request = self.factory.get('/api/checkout/unknown/')
        response = self.view(request, session_id='unknown')

        self.assertEqual(response.status_code, 200)


class TestUpdateQuantityView(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = UpdateQuantityView.as_view()

    @patch('checkout.views.session_views.CheckoutClient')
    def test_update_quantity_success_returns_200(self, mock_client_cls):
        mock_client = Mock()
        mock_client.update_quantity.return_value = {"checkoutSessionId": "session123"}
        mock_client_cls.return_value = mock_client

        payload = {"line_item_id": "li1", "quantity": 2}
        request = self.factory.post('/api/checkout/session123/update_quantity/', payload, format='json')
        response = self.view(request, session_id='session123')

        self.assertEqual(response.status_code, 200)

    def test_update_quantity_invalid_data_returns_400(self):
        payload = {"line_item_id": "li1", "quantity": 0}
        request = self.factory.post('/api/checkout/session123/update_quantity/', payload, format='json')
        response = self.view(request, session_id='session123')

        self.assertEqual(response.status_code, 400)

    @patch('checkout.views.session_views.CheckoutClient')
    def test_update_quantity_ebay_error_returns_502(self, mock_client_cls):
        mock_client = Mock()
        mock_client.update_quantity.return_value = {"error": "Error"}
        mock_client_cls.return_value = mock_client

        payload = {"line_item_id": "li1", "quantity": 2}
        request = self.factory.post('/api/checkout/session123/update_quantity/', payload, format='json')
        response = self.view(request, session_id='session123')

        self.assertEqual(response.status_code, 502)

    @patch('checkout.views.session_views.CheckoutClient')
    def test_update_quantity_updates_local_session(self, mock_client_cls):
        CheckoutSession.objects.create(
            ebay_session_id="session123",
            buyer_email="test@test.com",
            shipping_address={"city": "Test"},
            status='CREATED'
        )

        mock_client = Mock()
        mock_client.update_quantity.return_value = {
            "checkoutSessionId": "session123",
            "pricingSummary": {"total": {"value": "50.00"}}
        }
        mock_client_cls.return_value = mock_client

        payload = {"line_item_id": "li1", "quantity": 2}
        request = self.factory.post('/api/checkout/session123/update_quantity/', payload, format='json')
        self.view(request, session_id='session123')

        session = CheckoutSession.objects.get(ebay_session_id="session123")
        self.assertEqual(session.status, 'UPDATED')


class TestUpdateShippingOptionView(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = UpdateShippingOptionView.as_view()

    @patch('checkout.views.session_views.CheckoutClient')
    def test_update_shipping_success_returns_200(self, mock_client_cls):
        mock_client = Mock()
        mock_client.update_shipping_option.return_value = {"checkoutSessionId": "session123"}
        mock_client_cls.return_value = mock_client

        payload = {"line_item_id": "li1", "shipping_option_id": "ship1"}
        request = self.factory.post('/api/checkout/session123/update_shipping/', payload, format='json')
        response = self.view(request, session_id='session123')

        self.assertEqual(response.status_code, 200)

    def test_update_shipping_invalid_data_returns_400(self):
        payload = {"line_item_id": "li1"}
        request = self.factory.post('/api/checkout/session123/update_shipping/', payload, format='json')
        response = self.view(request, session_id='session123')

        self.assertEqual(response.status_code, 400)

    @patch('checkout.views.session_views.CheckoutClient')
    def test_update_shipping_ebay_error_returns_502(self, mock_client_cls):
        mock_client = Mock()
        mock_client.update_shipping_option.return_value = {"error": "Error"}
        mock_client_cls.return_value = mock_client

        payload = {"line_item_id": "li1", "shipping_option_id": "ship1"}
        request = self.factory.post('/api/checkout/session123/update_shipping/', payload, format='json')
        response = self.view(request, session_id='session123')

        self.assertEqual(response.status_code, 502)


class TestApplyCouponView(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ApplyCouponView.as_view()

    @patch('checkout.views.session_views.CheckoutClient')
    def test_apply_coupon_success_returns_200(self, mock_client_cls):
        mock_client = Mock()
        mock_client.apply_coupon.return_value = {"checkoutSessionId": "session123"}
        mock_client_cls.return_value = mock_client

        payload = {"redemption_code": "SAVE10"}
        request = self.factory.post('/api/checkout/session123/apply_coupon/', payload, format='json')
        response = self.view(request, session_id='session123')

        self.assertEqual(response.status_code, 200)

    def test_apply_coupon_invalid_data_returns_400(self):
        payload = {}
        request = self.factory.post('/api/checkout/session123/apply_coupon/', payload, format='json')
        response = self.view(request, session_id='session123')

        self.assertEqual(response.status_code, 400)

    @patch('checkout.views.session_views.CheckoutClient')
    def test_apply_coupon_ebay_error_returns_502(self, mock_client_cls):
        mock_client = Mock()
        mock_client.apply_coupon.return_value = {"error": "Error"}
        mock_client_cls.return_value = mock_client

        payload = {"redemption_code": "SAVE10"}
        request = self.factory.post('/api/checkout/session123/apply_coupon/', payload, format='json')
        response = self.view(request, session_id='session123')

        self.assertEqual(response.status_code, 502)

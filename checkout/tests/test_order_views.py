import unittest
from unittest.mock import Mock, patch
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from checkout.views.order_views import PlaceOrderView, PurchaseOrderDetailView
from checkout.models import CheckoutSession, PurchaseOrder


class TestPlaceOrderView(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = PlaceOrderView.as_view()

    @patch('checkout.views.order_views.CheckoutClient')
    def test_place_order_success_returns_201(self, mock_client_cls):
        CheckoutSession.objects.create(
            ebay_session_id="session123",
            buyer_email="test@test.com",
            shipping_address={"city": "Test"},
            total=38.38,
            currency='USD'
        )

        mock_client = Mock()
        mock_client.place_order.return_value = {"purchaseOrderId": "order123"}
        mock_client_cls.return_value = mock_client

        request = self.factory.post('/api/orders/place/session123/')
        response = self.view(request, session_id='session123')

        self.assertEqual(response.status_code, 201)

    @patch('checkout.views.order_views.CheckoutClient')
    def test_place_order_ebay_error_returns_502(self, mock_client_cls):
        mock_client = Mock()
        mock_client.place_order.return_value = {"error": "Payment failed"}
        mock_client_cls.return_value = mock_client

        request = self.factory.post('/api/orders/place/session123/')
        response = self.view(request, session_id='session123')

        self.assertEqual(response.status_code, 502)

    @patch('checkout.views.order_views.CheckoutClient')
    def test_place_order_creates_local_purchase_order(self, mock_client_cls):
        CheckoutSession.objects.create(
            ebay_session_id="session123",
            buyer_email="test@test.com",
            shipping_address={"city": "Test"},
            total=38.38,
            currency='USD'
        )

        mock_client = Mock()
        mock_client.place_order.return_value = {"purchaseOrderId": "order456"}
        mock_client_cls.return_value = mock_client

        request = self.factory.post('/api/orders/place/session123/')
        self.view(request, session_id='session123')

        self.assertTrue(PurchaseOrder.objects.filter(ebay_order_id="order456").exists())

    @patch('checkout.views.order_views.CheckoutClient')
    def test_place_order_updates_session_status_to_completed(self, mock_client_cls):
        CheckoutSession.objects.create(
            ebay_session_id="session123",
            buyer_email="test@test.com",
            shipping_address={"city": "Test"},
            total=38.38,
            currency='USD',
            status='CREATED'
        )

        mock_client = Mock()
        mock_client.place_order.return_value = {"purchaseOrderId": "order789"}
        mock_client_cls.return_value = mock_client

        request = self.factory.post('/api/orders/place/session123/')
        self.view(request, session_id='session123')

        session = CheckoutSession.objects.get(ebay_session_id="session123")
        self.assertEqual(session.status, 'COMPLETED')

    @patch('checkout.views.order_views.CheckoutClient')
    def test_place_order_works_without_local_session(self, mock_client_cls):
        mock_client = Mock()
        mock_client.place_order.return_value = {"purchaseOrderId": "order123"}
        mock_client_cls.return_value = mock_client

        request = self.factory.post('/api/orders/place/unknown_session/')
        response = self.view(request, session_id='unknown_session')

        self.assertEqual(response.status_code, 201)


class TestPurchaseOrderDetailView(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = PurchaseOrderDetailView.as_view()

    @patch('checkout.views.order_views.CheckoutClient')
    def test_get_order_returns_ebay_data(self, mock_client_cls):
        mock_client = Mock()
        expected = {"purchaseOrderId": "order123", "purchaseOrderStatus": "CONFIRMED"}
        mock_client.get_purchase_order.return_value = expected
        mock_client_cls.return_value = mock_client

        request = self.factory.get('/api/orders/order123/')
        response = self.view(request, order_id='order123')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected)

    @patch('checkout.views.order_views.CheckoutClient')
    def test_get_order_updates_local_record(self, mock_client_cls):
        session = CheckoutSession.objects.create(
            ebay_session_id="session123",
            buyer_email="test@test.com",
            shipping_address={"city": "Test"},
        )
        PurchaseOrder.objects.create(
            ebay_order_id="order123",
            checkout_session=session,
            status='PENDING'
        )

        mock_client = Mock()
        mock_client.get_purchase_order.return_value = {
            "purchaseOrderId": "order123",
            "purchaseOrderStatus": "CONFIRMED"
        }
        mock_client_cls.return_value = mock_client

        request = self.factory.get('/api/orders/order123/')
        self.view(request, order_id='order123')

        order = PurchaseOrder.objects.get(ebay_order_id="order123")
        self.assertIsNotNone(order.ebay_response)

    @patch('checkout.views.order_views.CheckoutClient')
    def test_get_order_ebay_error_returns_502(self, mock_client_cls):
        mock_client = Mock()
        mock_client.get_purchase_order.return_value = {"error": "Not found"}
        mock_client_cls.return_value = mock_client

        request = self.factory.get('/api/orders/order123/')
        response = self.view(request, order_id='order123')

        self.assertEqual(response.status_code, 502)

    @patch('checkout.views.order_views.CheckoutClient')
    def test_get_order_works_without_local_record(self, mock_client_cls):
        mock_client = Mock()
        mock_client.get_purchase_order.return_value = {"purchaseOrderId": "unknown"}
        mock_client_cls.return_value = mock_client

        request = self.factory.get('/api/orders/unknown/')
        response = self.view(request, order_id='unknown')

        self.assertEqual(response.status_code, 200)

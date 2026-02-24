import unittest
from unittest.mock import Mock, patch, mock_open
import os
from checkout.checkout_client import CheckoutClient, GUEST_ORDER_SCOPES, GUEST_CHECKOUT_BASE_URL


class TestCheckoutClientInit(unittest.TestCase):

    def test_init_sets_base_url(self):
        client = CheckoutClient()
        self.assertEqual(client.base_url, GUEST_CHECKOUT_BASE_URL)

    def test_init_sets_yaml_file_path(self):
        client = CheckoutClient()
        self.assertTrue(client.yaml_file_path.endswith('ebay.yaml'))


class TestCreateYamlSecrets(unittest.TestCase):

    @patch.dict(os.environ, {
        'APP_ID': 'test_app_id',
        'CERT_ID': 'test_cert_id',
        'DEV_ID': 'test_dev_id',
        'REDIRECT_URI': 'test_redirect_uri'
    })
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.dump')
    def test_create_yaml_secrets_writes_correct_content(self, mock_yaml_dump, mock_file):
        client = CheckoutClient()
        client._create_yaml_secrets()

        expected_secrets = {
            "api.ebay.com": {
                "appid": "test_app_id",
                "certid": "test_cert_id",
                "devid": "test_dev_id",
                "redirecturi": "test_redirect_uri"
            }
        }

        mock_file.assert_called_once_with(client.yaml_file_path, 'w')
        mock_yaml_dump.assert_called_once()
        actual_secrets = mock_yaml_dump.call_args[0][0]
        self.assertEqual(actual_secrets, expected_secrets)

    @patch.dict(os.environ, {}, clear=True)
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.dump')
    def test_create_yaml_secrets_handles_missing_env_vars(self, mock_yaml_dump, mock_file):
        client = CheckoutClient()
        client._create_yaml_secrets()

        actual_secrets = mock_yaml_dump.call_args[0][0]
        self.assertIsNone(actual_secrets["api.ebay.com"]["appid"])
        self.assertIsNone(actual_secrets["api.ebay.com"]["certid"])


class TestGetToken(unittest.TestCase):

    @patch('checkout.checkout_client.oauth2api')
    @patch('checkout.checkout_client.credentialutil')
    @patch('os.path.exists')
    def test_get_token_when_yaml_exists(self, mock_exists, mock_credutil, mock_oauth2api):
        mock_exists.return_value = True

        mock_token = Mock()
        mock_token.access_token = "test_access_token"
        mock_oauth_instance = Mock()
        mock_oauth_instance.get_application_token.return_value = mock_token
        mock_oauth2api.return_value = mock_oauth_instance

        client = CheckoutClient()
        token = client._get_token()

        self.assertEqual(token, "test_access_token")
        mock_credutil.load.assert_called_once_with(client.yaml_file_path)

    @patch('checkout.checkout_client.oauth2api')
    @patch('checkout.checkout_client.credentialutil')
    @patch('os.path.exists')
    @patch.object(CheckoutClient, '_create_yaml_secrets')
    def test_get_token_creates_yaml_when_missing(self, mock_create_yaml, mock_exists, mock_credutil, mock_oauth2api):
        mock_exists.return_value = False

        mock_token = Mock()
        mock_token.access_token = "test_access_token"
        mock_oauth_instance = Mock()
        mock_oauth_instance.get_application_token.return_value = mock_token
        mock_oauth2api.return_value = mock_oauth_instance

        client = CheckoutClient()
        client._get_token()

        mock_create_yaml.assert_called_once()

    @patch('checkout.checkout_client.oauth2api')
    @patch('checkout.checkout_client.credentialutil')
    @patch('os.path.exists')
    def test_get_token_uses_guest_order_scopes(self, mock_exists, mock_credutil, mock_oauth2api):
        mock_exists.return_value = True

        mock_token = Mock()
        mock_token.access_token = "test_access_token"
        mock_oauth_instance = Mock()
        mock_oauth_instance.get_application_token.return_value = mock_token
        mock_oauth2api.return_value = mock_oauth_instance

        client = CheckoutClient()
        client._get_token()

        actual_scopes = mock_oauth_instance.get_application_token.call_args[0][1]
        self.assertEqual(actual_scopes, GUEST_ORDER_SCOPES)


class TestGetHeaders(unittest.TestCase):

    @patch.object(CheckoutClient, '_get_token')
    def test_get_headers_includes_authorization(self, mock_token):
        mock_token.return_value = "test_token"
        client = CheckoutClient()
        headers = client._get_headers()
        self.assertEqual(headers['Authorization'], 'Bearer test_token')

    @patch.object(CheckoutClient, '_get_token')
    def test_get_headers_includes_content_type(self, mock_token):
        mock_token.return_value = "test_token"
        client = CheckoutClient()
        headers = client._get_headers()
        self.assertEqual(headers['Content-Type'], 'application/json')

    @patch.object(CheckoutClient, '_get_token')
    def test_get_headers_includes_marketplace_id(self, mock_token):
        mock_token.return_value = "test_token"
        client = CheckoutClient()
        headers = client._get_headers()
        self.assertEqual(headers['X-EBAY-C-MARKETPLACE-ID'], 'EBAY_US')


class TestInitiateCheckout(unittest.TestCase):

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.post')
    def test_initiate_checkout_success(self, mock_post, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        expected = {"checkoutSessionId": "session123", "lineItems": []}
        mock_response = Mock()
        mock_response.json.return_value = expected
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = CheckoutClient()
        result = client.initiate_checkout({"contactEmail": "test@test.com"})

        self.assertEqual(result, expected)

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.post')
    def test_initiate_checkout_calls_correct_url(self, mock_post, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = CheckoutClient()
        client.initiate_checkout({"contactEmail": "test@test.com"})

        called_url = mock_post.call_args[0][0]
        self.assertEqual(called_url, f'{GUEST_CHECKOUT_BASE_URL}/guest_checkout_session/initiate')

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.post')
    def test_initiate_checkout_returns_error_on_http_error(self, mock_post, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = __import__('requests').exceptions.HTTPError(response=mock_response)
        mock_response.json.return_value = {"message": "Bad Request"}
        mock_post.return_value = mock_response

        client = CheckoutClient()
        result = client.initiate_checkout({})

        self.assertIn('error', result)

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.post')
    def test_initiate_checkout_returns_error_on_exception(self, mock_post, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        mock_post.side_effect = Exception("Connection error")

        client = CheckoutClient()
        result = client.initiate_checkout({})

        self.assertIn('error', result)
        self.assertIn('Connection error', result['error'])


class TestGetCheckoutSession(unittest.TestCase):

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.get')
    def test_get_session_success(self, mock_get, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        expected = {"checkoutSessionId": "session123", "status": "ACTIVE"}
        mock_response = Mock()
        mock_response.json.return_value = expected
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CheckoutClient()
        result = client.get_checkout_session("session123")

        self.assertEqual(result, expected)

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.get')
    def test_get_session_calls_correct_url(self, mock_get, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CheckoutClient()
        client.get_checkout_session("session123")

        called_url = mock_get.call_args[0][0]
        self.assertEqual(called_url, f'{GUEST_CHECKOUT_BASE_URL}/guest_checkout_session/session123')

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.get')
    def test_get_session_returns_error_on_failure(self, mock_get, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        mock_get.side_effect = Exception("API Error")

        client = CheckoutClient()
        result = client.get_checkout_session("session123")

        self.assertIn('error', result)


class TestUpdateQuantity(unittest.TestCase):

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.post')
    def test_update_quantity_success(self, mock_post, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        expected = {"checkoutSessionId": "session123"}
        mock_response = Mock()
        mock_response.json.return_value = expected
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = CheckoutClient()
        result = client.update_quantity("session123", {"lineItemId": "li1", "quantity": 2})

        self.assertEqual(result, expected)

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.post')
    def test_update_quantity_calls_correct_url(self, mock_post, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = CheckoutClient()
        client.update_quantity("session123", {})

        called_url = mock_post.call_args[0][0]
        self.assertEqual(called_url, f'{GUEST_CHECKOUT_BASE_URL}/guest_checkout_session/session123/update_quantity')

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.post')
    def test_update_quantity_returns_error_on_failure(self, mock_post, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        mock_post.side_effect = Exception("Error")

        client = CheckoutClient()
        result = client.update_quantity("session123", {})

        self.assertIn('error', result)


class TestUpdateShippingOption(unittest.TestCase):

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.post')
    def test_update_shipping_success(self, mock_post, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        expected = {"checkoutSessionId": "session123"}
        mock_response = Mock()
        mock_response.json.return_value = expected
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = CheckoutClient()
        result = client.update_shipping_option("session123", {"lineItemId": "li1", "shippingOptionId": "ship1"})

        self.assertEqual(result, expected)

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.post')
    def test_update_shipping_calls_correct_url(self, mock_post, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = CheckoutClient()
        client.update_shipping_option("session123", {})

        called_url = mock_post.call_args[0][0]
        self.assertEqual(called_url, f'{GUEST_CHECKOUT_BASE_URL}/guest_checkout_session/session123/update_shipping_option')

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.post')
    def test_update_shipping_returns_error_on_failure(self, mock_post, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        mock_post.side_effect = Exception("Error")

        client = CheckoutClient()
        result = client.update_shipping_option("session123", {})

        self.assertIn('error', result)


class TestApplyCoupon(unittest.TestCase):

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.post')
    def test_apply_coupon_success(self, mock_post, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        expected = {"checkoutSessionId": "session123"}
        mock_response = Mock()
        mock_response.json.return_value = expected
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = CheckoutClient()
        result = client.apply_coupon("session123", {"redemptionCode": "SAVE10"})

        self.assertEqual(result, expected)

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.post')
    def test_apply_coupon_calls_correct_url(self, mock_post, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = CheckoutClient()
        client.apply_coupon("session123", {})

        called_url = mock_post.call_args[0][0]
        self.assertEqual(called_url, f'{GUEST_CHECKOUT_BASE_URL}/guest_checkout_session/session123/apply_coupon')

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.post')
    def test_apply_coupon_returns_error_on_failure(self, mock_post, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        mock_post.side_effect = Exception("Error")

        client = CheckoutClient()
        result = client.apply_coupon("session123", {})

        self.assertIn('error', result)


class TestPlaceOrder(unittest.TestCase):

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.post')
    def test_place_order_success(self, mock_post, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        expected = {"purchaseOrderId": "order123"}
        mock_response = Mock()
        mock_response.json.return_value = expected
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = CheckoutClient()
        result = client.place_order("session123")

        self.assertEqual(result, expected)

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.post')
    def test_place_order_calls_correct_url(self, mock_post, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = CheckoutClient()
        client.place_order("session123")

        called_url = mock_post.call_args[0][0]
        self.assertEqual(called_url, f'{GUEST_CHECKOUT_BASE_URL}/guest_checkout_session/session123/place_order')

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.post')
    def test_place_order_returns_error_on_failure(self, mock_post, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        mock_post.side_effect = Exception("Error")

        client = CheckoutClient()
        result = client.place_order("session123")

        self.assertIn('error', result)


class TestGetPurchaseOrder(unittest.TestCase):

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.get')
    def test_get_purchase_order_success(self, mock_get, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        expected = {"purchaseOrderId": "order123", "purchaseOrderStatus": "CONFIRMED"}
        mock_response = Mock()
        mock_response.json.return_value = expected
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CheckoutClient()
        result = client.get_purchase_order("order123")

        self.assertEqual(result, expected)

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.get')
    def test_get_purchase_order_calls_correct_url(self, mock_get, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CheckoutClient()
        client.get_purchase_order("order123")

        called_url = mock_get.call_args[0][0]
        self.assertEqual(called_url, f'{GUEST_CHECKOUT_BASE_URL}/guest_purchase_order/order123')

    @patch.object(CheckoutClient, '_get_headers')
    @patch('requests.get')
    def test_get_purchase_order_returns_error_on_failure(self, mock_get, mock_headers):
        mock_headers.return_value = {'Authorization': 'Bearer test'}
        mock_get.side_effect = Exception("Error")

        client = CheckoutClient()
        result = client.get_purchase_order("order123")

        self.assertIn('error', result)

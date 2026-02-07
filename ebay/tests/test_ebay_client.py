import unittest
from unittest.mock import Mock, patch, mock_open
import os
from ..ebay_client import EbayClient


class TestEbayClientInit(unittest.TestCase):

    def test_init_sets_charity_id(self):
        client = EbayClient("12345")
        self.assertEqual(client.charity_id, "12345")

    def test_init_sets_charity_url(self):
        client = EbayClient("12345")
        expected_url = "https://api.ebay.com/buy/browse/v1/item_summary/search?limit=200&offset=200&charity_ids=12345"
        self.assertEqual(client.charity_url, expected_url)

    def test_init_sets_yaml_file_path(self):
        client = EbayClient("12345")
        self.assertTrue(client.yaml_file_path.endswith("ebay.yaml"))

    def test_init_with_different_charity_ids(self):
        test_ids = ["11111", "99999", "abc123"]
        for charity_id in test_ids:
            client = EbayClient(charity_id)
            self.assertEqual(client.charity_id, charity_id)
            self.assertIn(charity_id, client.charity_url)


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
        client = EbayClient("12345")
        
        # Call private method
        client._EbayClient__create_yaml_secrets()
        
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
        client = EbayClient("12345")
        client._EbayClient__create_yaml_secrets()
        
        actual_secrets = mock_yaml_dump.call_args[0][0]
        self.assertIsNone(actual_secrets["api.ebay.com"]["appid"])
        self.assertIsNone(actual_secrets["api.ebay.com"]["certid"])
        self.assertIsNone(actual_secrets["api.ebay.com"]["devid"])
        self.assertIsNone(actual_secrets["api.ebay.com"]["redirecturi"])

    @patch.dict(os.environ, {
        'APP_ID': 'test_app_id',
        'CERT_ID': 'test_cert_id'
    }, clear=True)
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.dump')
    def test_create_yaml_secrets_handles_partial_env_vars(self, mock_yaml_dump, mock_file):
        client = EbayClient("12345")
        client._EbayClient__create_yaml_secrets()
        
        actual_secrets = mock_yaml_dump.call_args[0][0]
        self.assertEqual(actual_secrets["api.ebay.com"]["appid"], "test_app_id")
        self.assertEqual(actual_secrets["api.ebay.com"]["certid"], "test_cert_id")
        self.assertIsNone(actual_secrets["api.ebay.com"]["devid"])
        self.assertIsNone(actual_secrets["api.ebay.com"]["redirecturi"])


class TestGetEbayToken(unittest.TestCase):

    @patch('ebay.ebay_client.oauth2api')
    @patch('ebay.ebay_client.credentialutil')
    @patch('os.path.exists')
    def test_get_ebay_token_when_yaml_exists(self, mock_exists, mock_credutil, mock_oauth2api):
        mock_exists.return_value = True
        
        mock_token = Mock()
        mock_token.access_token = "test_access_token"
        mock_oauth_instance = Mock()
        mock_oauth_instance.get_application_token.return_value = mock_token
        mock_oauth2api.return_value = mock_oauth_instance
        
        client = EbayClient("12345")
        token = client._get_ebay_token()
        
        self.assertEqual(token, "test_access_token")
        mock_credutil.load.assert_called_once_with(client.yaml_file_path)

    @patch('ebay.ebay_client.oauth2api')
    @patch('ebay.ebay_client.credentialutil')
    @patch('os.path.exists')
    @patch.object(EbayClient, '_EbayClient__create_yaml_secrets')
    def test_get_ebay_token_creates_yaml_when_missing(
        self, mock_create_yaml, mock_exists, mock_credutil, mock_oauth2api
    ):
        mock_exists.return_value = False
        
        mock_token = Mock()
        mock_token.access_token = "test_access_token"
        mock_oauth_instance = Mock()
        mock_oauth_instance.get_application_token.return_value = mock_token
        mock_oauth2api.return_value = mock_oauth_instance
        
        client = EbayClient("12345")
        client._get_ebay_token()
        
        mock_create_yaml.assert_called_once()

    @patch('ebay.ebay_client.oauth2api')
    @patch('ebay.ebay_client.credentialutil')
    @patch('os.path.exists')
    def test_get_ebay_token_does_not_create_yaml_when_exists(
        self, mock_exists, mock_credutil, mock_oauth2api
    ):
        mock_exists.return_value = True
        
        mock_token = Mock()
        mock_token.access_token = "test_access_token"
        mock_oauth_instance = Mock()
        mock_oauth_instance.get_application_token.return_value = mock_token
        mock_oauth2api.return_value = mock_oauth_instance
        
        client = EbayClient("12345")
        
        with patch.object(EbayClient, '_EbayClient__create_yaml_secrets') as mock_create:
            client._get_ebay_token()
            mock_create.assert_not_called()

    @patch('ebay.ebay_client.oauth2api')
    @patch('ebay.ebay_client.credentialutil')
    @patch('os.path.exists')
    def test_get_ebay_token_uses_correct_scopes(self, mock_exists, mock_credutil, mock_oauth2api):
        mock_exists.return_value = True
        
        mock_token = Mock()
        mock_token.access_token = "test_access_token"
        mock_oauth_instance = Mock()
        mock_oauth_instance.get_application_token.return_value = mock_token
        mock_oauth2api.return_value = mock_oauth_instance
        
        client = EbayClient("12345")
        client._get_ebay_token()
        
        expected_scopes = ['https://api.ebay.com/oauth/api_scope']
        mock_oauth_instance.get_application_token.assert_called_once()
        actual_scopes = mock_oauth_instance.get_application_token.call_args[0][1]
        self.assertEqual(actual_scopes, expected_scopes)


class TestGetItems(unittest.TestCase):

    @patch.object(EbayClient, '_get_ebay_token')
    @patch('requests.get')
    def test_get_items_success(self, mock_get, mock_token):
        mock_token.return_value = "test_token"
        
        expected_response = {
            "itemSummaries": [
                {"itemId": "123", "title": "Test Item"}
            ]
        }
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response
        
        client = EbayClient("12345")
        result = client.getItems()
        
        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            client.charity_url,
            headers={"Authorization": "Bearer test_token"}
        )

    @patch.object(EbayClient, '_get_ebay_token')
    @patch('requests.get')
    def test_get_items_returns_error_on_request_exception(self, mock_get, mock_token):
        mock_token.return_value = "test_token"
        mock_get.side_effect = Exception("Connection error")
        
        client = EbayClient("12345")
        result = client.getItems()
        
        self.assertIn("error", result)
        self.assertIn("Connection error", result["error"])

    @patch.object(EbayClient, '_get_ebay_token')
    @patch('requests.get')
    def test_get_items_handles_token_error(self, mock_get, mock_token):
        mock_token.side_effect = Exception("Token error")
        
        client = EbayClient("12345")
        result = client.getItems()
        
        self.assertIn("error", result)
        self.assertIn("Token error", result["error"])

    @patch.object(EbayClient, '_get_ebay_token')
    @patch('requests.get')
    def test_get_items_returns_empty_list(self, mock_get, mock_token):
        mock_token.return_value = "test_token"
        
        expected_response = {"itemSummaries": []}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response
        
        client = EbayClient("12345")
        result = client.getItems()
        
        self.assertEqual(result, expected_response)

    @patch.object(EbayClient, '_get_ebay_token')
    @patch('requests.get')
    def test_get_items_handles_json_decode_error(self, mock_get, mock_token):
        mock_token.return_value = "test_token"
        
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        
        client = EbayClient("12345")
        result = client.getItems()
        
        self.assertIn("error", result)


class TestIsItemActive(unittest.TestCase):

    @patch.object(EbayClient, '_get_ebay_token')
    @patch('requests.get')
    def test_is_item_active_returns_true_when_in_stock(self, mock_get, mock_token):
        mock_token.return_value = "test_token"
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "estimatedAvailabilities": [
                {"estimatedAvailabilityStatus": "IN_STOCK"}
            ]
        }
        mock_get.return_value = mock_response
        
        client = EbayClient("12345")
        result = client.isItemActive("v1|123456|0")
        
        self.assertTrue(result)

    @patch.object(EbayClient, '_get_ebay_token')
    @patch('requests.get')
    def test_is_item_active_returns_false_when_out_of_stock(self, mock_get, mock_token):
        mock_token.return_value = "test_token"
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "estimatedAvailabilities": [
                {"estimatedAvailabilityStatus": "OUT_OF_STOCK"}
            ]
        }
        mock_get.return_value = mock_response
        
        client = EbayClient("12345")
        result = client.isItemActive("v1|123456|0")
        
        self.assertFalse(result)

    @patch.object(EbayClient, '_get_ebay_token')
    @patch('requests.get')
    def test_is_item_active_calls_correct_endpoint(self, mock_get, mock_token):
        mock_token.return_value = "test_token"
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "estimatedAvailabilities": [
                {"estimatedAvailabilityStatus": "IN_STOCK"}
            ]
        }
        mock_get.return_value = mock_response
        
        client = EbayClient("12345")
        client.isItemActive("v1|123456|0")
        
        mock_get.assert_called_once_with(
            "https://api.ebay.com/buy/browse/v1/item/v1|123456|0",
            headers={"Authorization": "Bearer test_token"}
        )

    @patch.object(EbayClient, '_get_ebay_token')
    @patch('requests.get')
    def test_is_item_active_returns_error_on_exception(self, mock_get, mock_token):
        mock_token.return_value = "test_token"
        mock_get.side_effect = Exception("API Error")
        
        client = EbayClient("12345")
        result = client.isItemActive("v1|123456|0")
        
        self.assertEqual(result, "error")

    @patch.object(EbayClient, '_get_ebay_token')
    @patch('requests.get')
    def test_is_item_active_returns_error_on_missing_data(self, mock_get, mock_token):
        mock_token.return_value = "test_token"
        
        mock_response = Mock()
        mock_response.json.return_value = {}  # Missing estimatedAvailabilities
        mock_get.return_value = mock_response
        
        client = EbayClient("12345")
        result = client.isItemActive("v1|123456|0")
        
        self.assertEqual(result, "error")

    @patch.object(EbayClient, '_get_ebay_token')
    @patch('requests.get')
    def test_is_item_active_returns_error_on_empty_availabilities(self, mock_get, mock_token):
        mock_token.return_value = "test_token"
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "estimatedAvailabilities": []
        }
        mock_get.return_value = mock_response
        
        client = EbayClient("12345")
        result = client.isItemActive("v1|123456|0")
        
        self.assertEqual(result, "error")

    @patch.object(EbayClient, '_get_ebay_token')
    @patch('requests.get')
    def test_is_item_active_handles_different_statuses(self, mock_get, mock_token):
        mock_token.return_value = "test_token"
        
        statuses_and_expected = [
            ("IN_STOCK", True),
            ("OUT_OF_STOCK", False),
            ("LIMITED_STOCK", False),
            ("UNAVAILABLE", False),
            ("DISCONTINUED", False),
        ]
        
        client = EbayClient("12345")
        
        for status, expected in statuses_and_expected:
            mock_response = Mock()
            mock_response.json.return_value = {
                "estimatedAvailabilities": [
                    {"estimatedAvailabilityStatus": status}
                ]
            }
            mock_get.return_value = mock_response
            
            result = client.isItemActive("v1|123456|0")
            self.assertEqual(result, expected, f"Failed for status: {status}")

    @patch.object(EbayClient, '_get_ebay_token')
    @patch('requests.get')
    def test_is_item_active_handles_token_error(self, mock_get, mock_token):
        mock_token.side_effect = Exception("Token retrieval failed")
        
        client = EbayClient("12345")
        result = client.isItemActive("v1|123456|0")
        
        self.assertEqual(result, "error")


class TestEbayClientIntegration(unittest.TestCase):

    @patch('ebay.ebay_client.oauth2api')
    @patch('ebay.ebay_client.credentialutil')
    @patch('os.path.exists')
    @patch('requests.get')
    def test_full_get_items_flow(self, mock_get, mock_exists, mock_credutil, mock_oauth2api):
 
        mock_exists.return_value = True
        mock_token = Mock()
        mock_token.access_token = "integration_test_token"
        mock_oauth_instance = Mock()
        mock_oauth_instance.get_application_token.return_value = mock_token
        mock_oauth2api.return_value = mock_oauth_instance
        
        expected_items = {
            "itemSummaries": [
                {"itemId": "item1", "title": "Item 1"},
                {"itemId": "item2", "title": "Item 2"}
            ]
        }
        mock_response = Mock()
        mock_response.json.return_value = expected_items
        mock_get.return_value = mock_response
        
        client = EbayClient("12345")
        result = client.getItems()
        
        self.assertEqual(result, expected_items)
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("Bearer integration_test_token", call_args[1]["headers"]["Authorization"])

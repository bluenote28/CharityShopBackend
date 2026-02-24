from ebay.oauthclient.oauth2api import oauth2api
from ebay.oauthclient.credentialutil import credentialutil
from ebay.oauthclient.model.model import environment
import os, requests, yaml, logging

logger = logging.getLogger(__name__)

GUEST_CHECKOUT_BASE_URL = 'https://apix.ebay.com/buy/order/v2'
GUEST_ORDER_SCOPES = [
    'https://api.ebay.com/oauth/api_scope',
    'https://api.ebay.com/oauth/api_scope/buy.guest.order'
]
MARKETPLACE_ID = 'EBAY_US'


class CheckoutClient:

    def __init__(self):
        self.base_url = GUEST_CHECKOUT_BASE_URL
        self.yaml_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'ebay', 'ebay.yaml'
        )

    def _create_yaml_secrets(self):
        secrets = {
            "api.ebay.com": {
                "appid": os.environ.get('APP_ID'),
                "certid": os.environ.get('CERT_ID'),
                "devid": os.environ.get('DEV_ID'),
                "redirecturi": os.environ.get('REDIRECT_URI')
            }
        }
        with open(self.yaml_file_path, 'w') as file:
            yaml.dump(secrets, file, default_flow_style=False)

    def _get_token(self):
        if not os.path.exists(self.yaml_file_path):
            self._create_yaml_secrets()

        credentialutil.load(self.yaml_file_path)
        oauth2api_inst = oauth2api()
        app_token = oauth2api_inst.get_application_token(
            environment.PRODUCTION, GUEST_ORDER_SCOPES
        )
        return app_token.access_token

    def _get_headers(self):
        token = self._get_token()
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
            'X-EBAY-C-MARKETPLACE-ID': MARKETPLACE_ID,
        }

    def initiate_checkout(self, payload):
        try:
            url = f'{self.base_url}/guest_checkout_session/initiate'
            headers = self._get_headers()
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"eBay checkout initiation failed: {e}")
            return {"error": str(e), "detail": e.response.json() if e.response else None}
        except Exception as e:
            logger.error(f"Error initiating checkout: {e}")
            return {"error": str(e)}

    def get_checkout_session(self, checkout_session_id):
        try:
            url = f'{self.base_url}/guest_checkout_session/{checkout_session_id}'
            headers = self._get_headers()
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"eBay get session failed: {e}")
            return {"error": str(e), "detail": e.response.json() if e.response else None}
        except Exception as e:
            logger.error(f"Error getting checkout session: {e}")
            return {"error": str(e)}

    def update_quantity(self, checkout_session_id, payload):
        try:
            url = f'{self.base_url}/guest_checkout_session/{checkout_session_id}/update_quantity'
            headers = self._get_headers()
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"eBay update quantity failed: {e}")
            return {"error": str(e), "detail": e.response.json() if e.response else None}
        except Exception as e:
            logger.error(f"Error updating quantity: {e}")
            return {"error": str(e)}

    def update_shipping_option(self, checkout_session_id, payload):
        try:
            url = f'{self.base_url}/guest_checkout_session/{checkout_session_id}/update_shipping_option'
            headers = self._get_headers()
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"eBay update shipping failed: {e}")
            return {"error": str(e), "detail": e.response.json() if e.response else None}
        except Exception as e:
            logger.error(f"Error updating shipping option: {e}")
            return {"error": str(e)}

    def apply_coupon(self, checkout_session_id, payload):
        try:
            url = f'{self.base_url}/guest_checkout_session/{checkout_session_id}/apply_coupon'
            headers = self._get_headers()
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"eBay apply coupon failed: {e}")
            return {"error": str(e), "detail": e.response.json() if e.response else None}
        except Exception as e:
            logger.error(f"Error applying coupon: {e}")
            return {"error": str(e)}

    def place_order(self, checkout_session_id):
        try:
            url = f'{self.base_url}/guest_checkout_session/{checkout_session_id}/place_order'
            headers = self._get_headers()
            response = requests.post(url, json={}, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"eBay place order failed: {e}")
            return {"error": str(e), "detail": e.response.json() if e.response else None}
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {"error": str(e)}

    def get_purchase_order(self, purchase_order_id):
        try:
            url = f'{self.base_url}/guest_purchase_order/{purchase_order_id}'
            headers = self._get_headers()
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"eBay get purchase order failed: {e}")
            return {"error": str(e), "detail": e.response.json() if e.response else None}
        except Exception as e:
            logger.error(f"Error getting purchase order: {e}")
            return {"error": str(e)}

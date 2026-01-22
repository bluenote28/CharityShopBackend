from .oauthclient.oauth2api import oauth2api
from .oauthclient.credentialutil import credentialutil
from .oauthclient.model.model import environment
import os, requests, yaml, logging
from yaml import dump

logger = logging.getLogger(__name__)

class EbayClient():

        def __init__(self, charity_ID):
                self.charity_id = charity_ID
                self.charity_url = f'https://api.ebay.com/buy/browse/v1/item_summary/search?limit=200&offset=200&charity_ids={charity_ID}'
                self.yaml_file_path = os.path.join(os.path.split(__file__)[0],'ebay.yaml')

        def __create_yaml_secrets(self):

                secrets = {"api.ebay.com" : {"appid": os.environ.get('APP_ID'), 
                                             "certid": os.environ.get('CERT_ID'),
                                             "devid": os.environ.get('DEV_ID'),
                                             "redirecturi": os.environ.get('REDIRECT_URI')}}
                
                with open(self.yaml_file_path, 'w') as file:
                        yaml.dump(secrets, file, default_flow_style=False)


        def _get_ebay_token(self):

                scopes = ['https://api.ebay.com/oauth/api_scope']

                if os.path.exists(self.yaml_file_path) == False:
                       self.__create_yaml_secrets()
                       
                credentialutil.load(self.yaml_file_path)
                oauth2api_inst = oauth2api()
                app_token = oauth2api_inst.get_application_token(environment.PRODUCTION, scopes)

                return app_token.access_token
        
        def getItems(self):
            try:
                token = self._get_ebay_token()
                logger.info(token)
                response = requests.get(f'{self.charity_url}', headers={"Authorization": f'Bearer {token}'})
                logger.info("response from ebay in ebay client: ", response.json())
                return response.json()
            except Exception as e:
                return {"error": f"Error fetching items from eBay API: {e}"}
            
        def isItemActive(self, item_id):
               try:
                   token = self._get_ebay_token()
                   response = requests.get(f'https://api.ebay.com/buy/browse/v1/item/{item_id}', headers={"Authorization": f'Bearer {token}'})
                   data = response.json()
                   
                   item_status = data['estimatedAvailabilities'][0]['estimatedAvailabilityStatus']

                   if item_status == "IN_STOCK":
                        return True
                   else:
                        return False

               except Exception as e:
                   print(f"Error fetching items from eBay API: {e}")
                   return "error"
               
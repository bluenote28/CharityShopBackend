import time
from .ebay_client import EbayClient
import logging
import traceback

logger = logging.getLogger(__name__)
WORD_FILTER = {'playboy', 'sexy'}

class DatabaseLoader():

    def __init__(self, charity_id):
        self.charity_id = charity_id
        self.client = EbayClient(charity_id)

    def __containsInvalidWord(self, title):

        for word in WORD_FILTER:
                
            if title.lower().find(word.lower()) > -1:
                return True
        return False
    
    def load_items_to_db(self):
        from .serializers import ItemSerializer
        from databasescripts.database_actions import itemInDatabase

        try:
            
            response = self.client.getItems()

            if "error" in response:
                raise Exception(response['error'])
            
            elif 'itemSummaries' in response:
           
                data = response["itemSummaries"]   

                for item in data:

                    if self.__containsInvalidWord(item['title']):
                        continue
                    elif item['adultOnly'] == True:
                        continue
                    elif itemInDatabase(item['itemId']) == True:
                        continue
                    else:

                        try:
                            single_item = {
                                "name": item["title"],
                                "price": item["price"]["value"],
                                "shipping_price": item['shippingOptions'][0]['shippingCost']['value'],
                                "img_url": item["thumbnailImages"][0]["imageUrl"],
                                "additional_images": item['additionalImages'],
                                "web_url": item["itemWebUrl"],
                                "charity": self.charity_id,
                                "category": item["categories"][1]["categoryName"],
                                "category_list": item["categories"],
                                "ebay_id": item["itemId"],
                                "condition": item['condition'],
                                "item_location": item['itemLocation'],
                                "seller": item["seller"]
                            }

                        except KeyError as e:
                            logger.error(f"Key key error for item {item}: {e}")
                            continue
                        
                        except Exception as e:
                            logger.error(f"Error processing item {item['itemId']}: {e}")
                            continue
                    
                    serializer = ItemSerializer(data=single_item)

                    if serializer.is_valid():
                        serializer.save()
                    else:
                        logger.error(f"Serializer validation failed: {serializer.errors}")
                        logger.error(item)

                if 'next' in response:
                    time.sleep(90)
                    self.client.charity_url = response['next']
                    self.load_items_to_db()

            return "Success"
             
        except Exception as e:
            logger.error(f"Error loading items to database: {e}")
            logger.error(traceback.format_exc())
            return str(e)
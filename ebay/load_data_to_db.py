import time
from .ebay_client import EbayClient
import logging
import traceback

logger = logging.getLogger(__name__)
WORD_FILTER = {'playboy', 'sexy'}
ITEM_FIELDS = ["shipping_price","img_url","additional_images", "condition"]

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

                            single_item = {"name": item["title"], "price": item["price"]["value"], "web_url": item["web_url"], "charity": self.charity_id,"category": item["categories"][1]["categoryName"],
                                "category_list": item["categories"],"ebay_id": item["itemId"], "item_location": item['itemLocation'],"seller": item["seller"]}

                            for field in ITEM_FIELDS:

                                if field == "shipping_price":
                                    try:
                                        single_item["shipping_price"] = item['shippingOptions'][0]['shippingCost']['value']
                                    except:
                                        single_item["shipping_price"] = None

                                elif field == "img_url":
                                    try:
                                        single_item["img_url"] = item["thumbnailImages"][0]["imageUrl"]
                                    except:
                                        single_item["img_url"] = None

                                elif field == 'additionalImages':
                                    try:
                                        single_item['additionalImages'] = item['additionalImages']
                                    except:
                                        single_item['additionalImages'] = []
                                elif field == "condition":
                                    try:
                                        single_item["condition"] = item["condition"]
                                    except:
                                        single_item["condition"] = None
                        
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
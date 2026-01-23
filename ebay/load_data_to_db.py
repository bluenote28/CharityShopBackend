import time
from .ebay_client import EbayClient
import logging
import traceback

logger = logging.getLogger(__name__)
WORD_FILTER = {'playboy', 'sexy', 'sexual', 'sex'}

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
            logger.info("starting load database script")
            response = self.client.getItems()

            if "error" in response:
                raise Exception(response['error'])
            
            elif 'itemSummaries' in response:
           
                next_page = True

                while next_page:

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

                                single_item = {"name": item["title"], "price": item["price"]["value"], "web_url": item["itemWebUrl"], "charity": self.charity_id,"category": item["categories"][1]["categoryName"],
                                    "category_list": item["categories"],"ebay_id": item["itemId"], "item_location": item['itemLocation'],"seller": item["seller"]}
                                
                                try:
                                    single_item["shipping_price"] = item['shippingOptions'][0]['shippingCost']['value']
                                except:
                                    single_item["shipping_price"] = None
                                try:
                                    single_item["img_url"] = item["thumbnailImages"][0]["imageUrl"]
                                except:
                                    single_item["img_url"] = None

                                try:
                                    single_item['additional_images'] = {"additionalImages": item['additionalImages']}
                                except:
                                    single_item['additional_images'] = {"additionalImages":[]}
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
                            logger.info("sleeping for next call")
                            time.sleep(5)
                            self.client.charity_url = response['next']
                            response = self.client.getItems()
                        else:
                            next_page = False

            return "success"
             
        except Exception as e:
            logger.error(f"Error loading items to database: {e}")
            logger.error(traceback.format_exc())
            return str(e)
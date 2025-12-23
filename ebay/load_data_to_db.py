import time
from .ebay_client import EbayClient
from .models import Item
from databasescripts.database_actions import deleteCharity, addCharity, itemInDatabase

WORD_FILTER = {'playboy'}

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
        from .models import Charity
        from .serializers import ItemSerializer
        
        print("Loading items to database...")

        try:
            
            response = self.client.getItems()
            
            if 'itemSummaries' in response:
           
                data = response["itemSummaries"]     

                for item in data:

                    if self.__containsInvalidWord(item['title']):
                        continue
                    elif item['adultOnly'] == True:
                        continue
                    elif itemInDatabase(item['itemId']):
                        print("cuirrent item")
                        continue
                    else:

                        print("new item")

                        try:
                            single_item = {
                                "name": item["title"],
                                "price": item["price"]["value"],
                                "img_url": item["thumbnailImages"][0]["imageUrl"],
                                "web_url": item["itemWebUrl"],
                                "charity": self.charity_id,
                                "category": item["categories"][1]["categoryName"],
                                "ebay_id": item["itemId"]
                            }

                        except KeyError:
                            single_item = {
                                "name": item["title"],
                                "price": item["price"]["value"],
                                "img_url": "",
                                "web_url": item["itemWebUrl"],
                                "charity": self.charity_id,
                                "category": item["categories"][1]["categoryName"],
                                "ebay_id": item["itemId"]
                            }
                    
                    serializer = ItemSerializer(data=single_item)

                    if serializer.is_valid():
                        serializer.save()

                if 'next' in response:
                    time.sleep(90)
                    self.client.charity_url = response['next']
                    self.load_items_to_db()

            return "Success"
             
        except Exception as e:
            return str(e)
        

    def refresh_charity_items(self):

        current_items = Item.objects.all(charity=self.charity_id)

        self.load_items_to_db()




         


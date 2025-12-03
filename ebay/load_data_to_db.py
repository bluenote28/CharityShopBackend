import time
from .serializers import ItemSerializer
from .ebay_client import EbayClient
from .models import Item, Charity

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

        try:

            if Charity.objects.filter(id=self.charity_id).exists():
                Charity.objects.get(id=self.charity_id).items.all().delete()
            
            response = self.client.getItems()
            
            if 'itemSummaries' in response:
           
                data = response["itemSummaries"]     

                for item in data:

                    if self.__containsInvalidWord(item['title']):
                        continue
                    elif item['adultOnly'] == True:
                        continue
                    else:

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
                    
    def update_database(self):
        
        all_charities = Charity.objects.all()

        for charity in all_charities:
            self.client.charity_id = charity.id
            self.load_items_to_db()
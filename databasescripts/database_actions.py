from ebay.models import Charity, Item
from ebay.serializers import CharitySerializer
import logging

logger = logging.getLogger(__name__)

def deleteCharity(id):
     
    try: 
        charity = Charity.objects.get(id=id)
        charity.delete()
        return "Success"
    except Exception as e:
        print(f"Error deleting charity: {e}")
        return e

def addCharity(charity_data):

    serializer = CharitySerializer(data=charity_data)
    if serializer.is_valid():
        serializer.save()
        return "Success"
    else:
        return "Failure"
    
def itemInDatabase(item_id):

   try: 
        item = Item.objects.get(ebay_id=item_id)
        return True

   except Item.DoesNotExist:
       return False
   
   except Exception as e:
       print(e)

def retrieveItem(item_id):

   try: 
        item = Item.objects.get(ebay_id=item_id)
        return item

   except Item.DoesNotExist:
       return None
   
   except Exception as e:
       print(e)

def getItemsByCategory(category_id):

    try: 
        items = Item.objects.filter(category=category_id)
        return items
    except Exception as e:
        print(f"Error retrieving items by category: {e}")
        return []
    
def deleteItemFromDatabase(item_id):

    try:
        Item.objects.delete(ebay_id=item_id)
        logger.info(f"Deleted {item_id} from the database")
        
        return "Success"
    except Exception as e:
        print(f"Error deleting item from database: {e}")
        return "Failure"
    

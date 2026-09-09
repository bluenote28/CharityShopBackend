from ebay.models import Charity, Item
from ebay.serializers import CharitySerializer
from django.contrib.postgres.search import SearchQuery
from django.db import connection
import logging, datetime

logger = logging.getLogger(__name__)


def _filter_by_category_name(queryset, category_name):
    if connection.features.supports_json_field_contains:
        return queryset.filter(category_list__contains=[{"categoryName": category_name}])
    return queryset.filter(category_list__icontains=f'"categoryName": "{category_name}"')

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
        return serializer.errors
    
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
        item = retrieveItem(item_id)
        item.delete()
        logger.info(f"Deleted {item_id} from the database")

        return "Success"
    except Exception as e:
        print(f"Error deleting item from database: {e}")
        return "Failure"
    
def getItemsBySubCategory(subcategory):
    
    try:
        items = Item.objects.filter(category_list__contains=[{"categoryName": subcategory}])
        return items
    
    except Exception as e:
        print(f'Error retrieving items by sub category')
        return "Failure"

def getItemsByFilter(subcategory, filter=None, search=None):
    try:
         items = Item.objects.filter(category_list__contains=[{"categoryName": subcategory}])
         if filter:
             items = items.filter(category_list__contains=[{"categoryName": filter}])
         query = (search or "").strip()
         if query:
             items = items.filter(
                 search_vector=SearchQuery(query, search_type="plain", config="english")
             )
         return items
    except Exception as e:
        print(f'Error retrieving items by filter')
        return "Failure"

def getItemsByCharity(charity_id, category=None):
    try:
        items = Item.objects.filter(charity_id=charity_id)
        if category:
            items = _filter_by_category_name(items, category)
        return items
    except Exception as e:
        print(f'Error retrieving items by charity: {e}')
        return "Failure"

def updateCharityUpdatedAt(charity_id):
    current_date = datetime.date.today()
    charity = Charity.objects.get(id=charity_id)
    charity.updated_at = current_date
    charity.save()
    

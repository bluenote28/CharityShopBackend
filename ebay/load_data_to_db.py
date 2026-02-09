import time
from .ebay_client import EbayClient
import logging
import traceback
from django.db import connection, transaction

logger = logging.getLogger(__name__)
WORD_FILTER = {'playboy','play boy', 'penthouse', 'skin art magazine', 
'sexy', 'sexual', 'sex', 'orlies lowriding', 'easyriders',
'sports illustrated swimsuit', 'swim suit edition', 
'national lampoon humor magazine', 'red sonja', 'fhm magazine'}

class DatabaseLoader():

    def __init__(self, charity_id):
        self.charity_id = charity_id
        self.client = EbayClient(charity_id)
        self.items_processed = 0
        self.items_saved = 0
        self.items_skipped = 0

    def __containsInvalidWord(self, title):
        title_lower = title.lower()
        return any(word in title_lower for word in WORD_FILTER)
    
    def __process_item(self, item):

        try:
            if self.__containsInvalidWord(item['title']):
                return None
            if item.get('adultOnly', False):
                return None

            single_item = {
                "name": item["title"],
                "price": item["price"]["value"],
                "web_url": item["itemWebUrl"],
                "charity": self.charity_id,
                "category": item["categories"][1]["categoryName"],
                "category_list": item.get("categories", []),
                "ebay_id": item["itemId"],
                "item_location": item.get('itemLocation'),
                "seller": item.get("seller"),
                "shipping_price": None,
                "img_url": None,
                "additional_images": {"additionalImages": []},
                "condition": item.get("condition"),
            }

            if 'shippingOptions' in item and item['shippingOptions']:
                single_item["shipping_price"] = item['shippingOptions'][0].get('shippingCost', {}).get('value')

            if 'thumbnailImages' in item and item['thumbnailImages']:
                single_item["img_url"] = item['thumbnailImages'][0].get("imageUrl")

            if 'additionalImages' in item:
                single_item['additional_images'] = {"additionalImages": item['additionalImages']}

            return single_item

        except Exception as e:
            logger.error(f"Error processing item {item.get('itemId', 'unknown')}: {e}")
            return None
        
    def __get_existing_ebay_ids(self, ebay_ids):
        from ebay.models import Item
        
        existing = Item.objects.filter(
            ebay_id__in=ebay_ids
        ).values_list('ebay_id', flat=True)
        
        return set(existing)
    
    def __save_items_batch(self, items_to_save):
        from .serializers import ItemSerializer
        
        saved_count = 0
        
        with transaction.atomic():
            for item_data in items_to_save:
                serializer = ItemSerializer(data=item_data)
                if serializer.is_valid():
                    serializer.save()
                    saved_count += 1
                else:
                    logger.warning(f"Validation failed for {item_data.get('ebay_id')}: {serializer.errors}")
        
        return saved_count
    
    def load_items_to_db(self):
        try:
            logger.info(f"Starting load database script for charity {self.charity_id}")
            response = self.client.getItems()

            if "error" in response:
               raise Exception(response['error'])
            
            if 'itemSummaries' not in response:
                logger.info("No items found in response")
                return "success - no items"
             
            page_count = 0

            while True:
                page_count += 1
                data = response.get("itemSummaries")
                
                if not data:
                    logger.info("No more items to process")
                    break
                
                logger.info(f"Processing page {page_count} with {len(data)} items")

                ebay_ids = [item['itemId'] for item in data]
                existing_ids = self.__get_existing_ebay_ids(ebay_ids)
                
                items_to_save = []
                for item in data:
                    self.items_processed += 1
                    
                    if item['itemId'] in existing_ids:
                        self.items_skipped += 1
                        continue
                    
                    processed_item = self.__process_item(item)
                    if processed_item:
                        items_to_save.append(processed_item)
                    else:
                        self.items_skipped += 1

                if items_to_save:
                    saved = self.__save_items_batch(items_to_save)
                    self.items_saved += saved
                    logger.info(f"Saved {saved} items from page {page_count}")

                connection.close()

                if 'next' in response:
                    logger.info(f"Fetching next page, sleeping 5 seconds...")
                    time.sleep(5)
                    self.client.charity_url = response['next']
                    response = self.client.getItems()
                else:
                    logger.info("No more pages")
                    break

            logger.info(
                f"Completed: processed={self.items_processed}, "
                f"saved={self.items_saved}, skipped={self.items_skipped}"
            )
            return "success"

        except Exception as e:
            logger.error(f"Error loading items to database: {e}")
            logger.error(traceback.format_exc())
            return str(e)
        
        finally:
            connection.close()

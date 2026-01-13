from ebay.models import Item
import logging
from .database_actions import deleteItemFromDatabase
from ebay.ebay_client import EbayClient
import datetime

logger = logging.getLogger(__name__)
DAYS_WITHOUT_CHECKING = 7


def deleteInactiveItems():

    client = EbayClient("")
    count = 0
    deleted = 0

    try:

        current_date = datetime.date.today()

        items = Item.objects.filter(updated_at__lte=current_date - datetime.timedelta(days=DAYS_WITHOUT_CHECKING))

        for item in items:

            item_is_active = client.isItemActive(item.ebay_id)

            if item_is_active == True:
                item.updated_at = current_date
                Item.save(item)
                count += 1
            elif item_is_active == "error":
                logger.error(f"Error retrieving item {item}")
                count += 1
                continue
            else:
                deleteItemFromDatabase(item.ebay_id)
                count += 1
                deleted += 1

        logger.info(f"processed {count} items.")
        logger.info(f"deleted {deleted} items")

    except Exception as e:
        logger.error(f"Error removing items from database {e}")
        logger.info(f"processed {count} items.")
        logger.info(f"deleted {deleted} items")
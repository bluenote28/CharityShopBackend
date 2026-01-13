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

    try:

        current_date = datetime.today()

        items = Item.objects.filter(updated_at__lte=current_date - datetime.timedelta(days=DAYS_WITHOUT_CHECKING))

        for item in items:

            item_is_active = client.isItemActive(item.ebay_id)

            if item_is_active:
                item.updated_at = current_date
                Item.save(item)
                count += 1
            else:
                deleteItemFromDatabase(item)
                count += 1

        logger.info(f"processed {count} items.")

    except Exception as e:
        logger.error(f"Error removing items from database {e}")
        logger.info(f"processed {count} items.")
from ebay.models import Item
import logging
from .database_actions import deleteItemFromDatabase
from ebay.ebay_client import EbayClient
import datetime

logger = logging.getLogger(__name__)
DAYS_WITHOUT_CHECKING = 7


def deleteInactiveItems():

    client = EbayClient("")

    try:

        items = Item.objects.get()

        current_date = datetime.date.today()

        for item in items:

            if current_date - item['updated_at'] <= DAYS_WITHOUT_CHECKING:
                logger.info(f"skipping item {item}")
                continue

            item_is_active = client.isItemActive(item['ebay_id'])

            if item_is_active:
                item['updated_at'] = current_date
                Item.save(item)
            else:
                deleteItemFromDatabase(item)

    except Exception as e:
        logger.error(f"Error removing items from database {e}")
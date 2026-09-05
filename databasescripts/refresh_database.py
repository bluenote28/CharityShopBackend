import logging
import datetime

logger = logging.getLogger(__name__)
DAYS_SINCE_CHECKING = 7


def deleteInactiveItems(items):
    from ebay.models import Item
    from ebay.ebay_client import EbayClient
    from .database_actions import deleteItemFromDatabase

    client = EbayClient("")
    count = 0
    deleted = 0

    try:

        for item in items:

            item_is_active = client.isItemActive(item.ebay_id)

            if item_is_active == True:
                count += 1
            elif item_is_active == "error":
                deleteItemFromDatabase(item.ebay_id)
                count += 1
                deleted += 1
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


def refreshDatabase(charity_id=None):
    from ebay.models import Item, FavoriteList, Charity
    from ebay.load_data_to_db import DatabaseLoader
    from .database_actions import updateCharityUpdatedAt

    if charity_id is None:
        favoriteLists = FavoriteList.objects.filter(items__isnull=False)
        items = set()
        for favoriteList in favoriteLists:
            for item in favoriteList.items.all():
                items.add(item)

        deleteInactiveItems(items)

        for charity in Charity.objects.all():
            if datetime.now() - charity.updated_at > datetime.timedelta(days=DAYS_SINCE_CHECKING):
                logger.info(f"charity {charity.name} has been updated in the last {DAYS_SINCE_CHECKING} days, skipping")
                continue

            logger.info(f"refreshing charity {charity.name}")
            Item.objects.filter(charity=charity).exclude(id__in=[item.id for item in items]).delete()
            loader = DatabaseLoader(charity.id)
            loader.load_items_to_db()
            updateCharityUpdatedAt(charity.id)

    else:

        favoriteLists = FavoriteList.objects.filter(items__isnull=False, items__charity=charity_id)
        items = set()
        for favoriteList in favoriteLists:
            for item in favoriteList.items.all():
                items.add(item)

        deleteInactiveItems(items)

        logger.info(f"refreshing charity {charity_id}")
        Item.objects.filter(charity=charity_id).exclude(id__in=[item.id for item in items]).delete()
        loader = DatabaseLoader(charity_id)
        loader.load_items_to_db()
        updateCharityUpdatedAt(charity_id)


    



        

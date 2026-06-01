from ebay.models import Item
from ebay.constants import FILTER_OPTIONS
from databasescripts.database_actions import getItemsByFilter


def search(query):

    if query.title() in FILTER_OPTIONS.keys():
        return getItemsByFilter(FILTER_OPTIONS[query.title()][0], FILTER_OPTIONS[query.title()][1])
        
    return Item.objects.filter(name__icontains=query)
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F

from databasescripts.database_actions import _filter_by_category_name
from ebay.models import Item


def search(query, charity_id=None, category=None):
    query = (query or "").strip()
    if not query:
        return Item.objects.none()

    search_query = SearchQuery(query, search_type="plain", config="english")
    items = Item.objects.filter(search_vector=search_query)
    if charity_id is not None:
        items = items.filter(charity_id=charity_id)
    if category:
        items = _filter_by_category_name(items, category)
    return (
        items
        .annotate(rank=SearchRank(F("search_vector"), search_query))
        .order_by("-rank")
    )
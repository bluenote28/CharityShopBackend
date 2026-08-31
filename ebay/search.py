from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F

from ebay.models import Item


def search(query):
    query = (query or "").strip()
    if not query:
        return Item.objects.none()

    search_query = SearchQuery(query, search_type="plain", config="english")
    return (
        Item.objects.filter(search_vector=search_query)
        .annotate(rank=SearchRank(F("search_vector"), search_query))
        .order_by("-rank")
    )
from ebay.models import Item
from ebay.constants import FILTER_OPTIONS
from django.contrib.postgres.search import SearchVector,SearchQuery

def inFilterOptions(query):
    return query.title() in FILTER_OPTIONS.keys()

def search(query):
    search_query = SearchQuery(query, search_type='plain')

    if inFilterOptions(query):
        name_vector = SearchVector('name', weight='B')
        category_vector = SearchVector('category', weight='A')
        description_vector = SearchVector('seller_description', weight='C')
    else:
        name_vector = SearchVector('name', weight='B')
        category_vector = SearchVector('category', weight='C')
        description_vector = SearchVector('seller_description', weight='A')

    search_vector = name_vector + category_vector + description_vector

    return Item.objects.annotate(search=search_vector).filter(search=search_query)
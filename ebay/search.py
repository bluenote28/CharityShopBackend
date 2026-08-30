from ebay.models import Item
from django.contrib.postgres.search import SearchVector,SearchQuery

def search(query):

    search_query = SearchQuery(query, search_type='plain')
        
    return Item.objects.annotate(search=SearchVector('name', 'seller_description', 'category')).filter(search=search_query)
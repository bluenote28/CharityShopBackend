from rest_framework.views import APIView
from rest_framework.response import Response
from ebay.models import Item
from ebay.serializers import ItemSerializer
from databasescripts.database_actions import retrieveItem, getItemsBySubCategory, getItemsByFilter
from rest_framework.pagination import PageNumberPagination
from django.core.cache import caches

disk = caches['diskcache']
ITEM_DETAIL_TTL = 60 * 30
ITEM_SEARCH_TTL = 60 * 15
ITEM_CATEGORY_TTL = 60 * 1440

class EbayCharityItems(APIView):

    paginator = PageNumberPagination()
    paginator.page_size = 50

    def get(self, request, item_id=None, search_text=None, category_id=None, filter=None):

        if item_id is not None:
            cache_key = f'item_{item_id}'
            cached = disk.get(cache_key)
            if cached is not None:
                return Response(cached)

            item = retrieveItem(item_id)
            if item is not None:
                serializer = ItemSerializer(item)
                disk.set(cache_key, serializer.data, ITEM_DETAIL_TTL)
                return Response(serializer.data)
            else:
                return Response("Item not found", status=404)

        elif search_text is not None:
            page = request.query_params.get('page', 1)
            cache_key = f'items_search_{search_text}_p{page}'
            cached = disk.get(cache_key)
            if cached is not None:
                return Response(cached)

            items = Item.objects.filter(name__icontains=search_text)
            paginated_items = self.paginator.paginate_queryset(items, request, self)
            serializer = ItemSerializer(paginated_items, many=True)
            response = self.paginator.get_paginated_response(serializer.data)
            disk.set(cache_key, response.data, ITEM_SEARCH_TTL)
            return response

        elif category_id is not None:
            page = request.query_params.get('page', 1)

            if filter is None:
                cache_key = f'items_cat_{category_id}_p{page}'
                cached = disk.get(cache_key)
                if cached is not None:
                    return Response(cached)

                items = getItemsBySubCategory(category_id)
                paginated_items = self.paginator.paginate_queryset(items, request, self)
                serializer = ItemSerializer(paginated_items, many=True)
                response = self.paginator.get_paginated_response(serializer.data)
                disk.set(cache_key, response.data, ITEM_CATEGORY_TTL)
                return response
            else:
                cache_key = f'items_cat_{category_id}_f_{filter}_p{page}'
                cached = disk.get(cache_key)
                if cached is not None:
                    return Response(cached)

                items = getItemsByFilter(category_id, filter)
                paginated_items = self.paginator.paginate_queryset(items, request, self)
                serializer = ItemSerializer(paginated_items, many=True)
                response = self.paginator.get_paginated_response(serializer.data)
                disk.set(cache_key, response.data, ITEM_CATEGORY_TTL)
                return response

        else:
            return Response("Please provide an item_id, search_text, or category_id", status=400)
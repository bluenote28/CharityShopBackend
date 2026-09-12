from rest_framework.views import APIView
from rest_framework.response import Response
from ebay.models import Item
from ebay.serializers import ItemSerializer
from databasescripts.database_actions import retrieveItem, getItemsBySubCategory, getItemsByFilter, getItemsByCharity
from rest_framework.pagination import PageNumberPagination
from django.core.cache import caches
from ebay.search import search
from ebay import ebay_client

disk = caches['diskcache']
ITEM_DETAIL_TTL = 60 * 30
ITEM_SEARCH_TTL = 60 * 15
ITEM_CATEGORY_TTL = 60 * 1440


def _parse_charity_ids(request):
    raw = request.query_params.get('charity_ids') or ''
    ids = []
    for part in raw.split(','):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return ids


def _apply_charity_ids(items, charity_ids):
    if not charity_ids:
        return items
    filter_fn = getattr(items, 'filter', None)
    if not callable(filter_fn):
        return items
    return items.filter(charity_id__in=charity_ids)


def _charity_ids_cache_suffix(charity_ids):
    if not charity_ids:
        return ''
    return '_cids_' + '_'.join(str(i) for i in sorted(charity_ids))

class EbayCharityItems(APIView):

    paginator = PageNumberPagination()
    paginator.page_size = 50

    def get(self, request, item_id=None, search_text=None, category_id=None, filter=None, charity_id=None):
        if category_id is None:
            category_id = request.query_params.get('category') or None
        if filter is None:
            filter = request.query_params.get('filter') or None
        search_query = request.query_params.get('search') or None
        charity_ids = _parse_charity_ids(request)

        if item_id is not None:
            cache_key = f'item_{item_id}'
            cached = disk.get(cache_key)
            if cached is not None:
                return Response(cached)

            item = retrieveItem(item_id)

            if item is None:
                return Response("Item not found", status=404)

            if item.donation_percentage is None:
                client = ebay_client.EbayClient(1234567890)
                item_details = client.getItemDetails(item_id)
                item.donation_percentage = item_details['donation_percentage']
                item.seller_description = item_details['seller_description']
                item.save()

            serializer = ItemSerializer(item)
            disk.set(cache_key, serializer.data, ITEM_DETAIL_TTL)
            return Response(serializer.data)

        elif charity_id is not None:
            page = request.query_params.get('page', 1)
            category = request.query_params.get('category') or None

            if search_text is not None:
                cache_key = f'items_charity_{charity_id}_search_{search_text}_p{page}'
                if category:
                    cache_key = f'items_charity_{charity_id}_search_{search_text}_c_{category}_p{page}'
                cached = disk.get(cache_key)
                if cached is not None:
                    return Response(cached)

                if category:
                    items = search(search_text, charity_id=charity_id, category=category)
                else:
                    items = search(search_text, charity_id=charity_id)
                paginated_items = self.paginator.paginate_queryset(items, request, self)
                serializer = ItemSerializer(paginated_items, many=True)
                response = self.paginator.get_paginated_response(serializer.data)
                disk.set(cache_key, response.data, ITEM_SEARCH_TTL)
                return response

            cache_key = f'items_charity_{charity_id}_p{page}'
            if category:
                cache_key = f'items_charity_{charity_id}_c_{category}_p{page}'
            cached = disk.get(cache_key)
            if cached is not None:
                return Response(cached)

            if category:
                items = getItemsByCharity(charity_id, category=category)
            else:
                items = getItemsByCharity(charity_id)
            paginated_items = self.paginator.paginate_queryset(items, request, self)
            serializer = ItemSerializer(paginated_items, many=True)
            response = self.paginator.get_paginated_response(serializer.data)
            disk.set(cache_key, response.data, ITEM_CATEGORY_TTL)
            return response

        elif search_text is not None:
            page = request.query_params.get('page', 1)
            cache_key = f'items_search_{search_text}{_charity_ids_cache_suffix(charity_ids)}_p{page}'
            cached = disk.get(cache_key)
            if cached is not None:
                return Response(cached)

            if charity_ids:
                items = search(search_text, charity_ids=charity_ids)
            else:
                items = search(search_text)
            paginated_items = self.paginator.paginate_queryset(items, request, self)
            serializer = ItemSerializer(paginated_items, many=True)
            response = self.paginator.get_paginated_response(serializer.data)
            disk.set(cache_key, response.data, ITEM_SEARCH_TTL)
            return response

        elif category_id is not None:
            page = request.query_params.get('page', 1)
            charity_suffix = _charity_ids_cache_suffix(charity_ids)

            if filter is None and search_query is None:
                cache_key = f'items_cat_{category_id}{charity_suffix}_p{page}'
                cached = disk.get(cache_key)
                if cached is not None:
                    return Response(cached)

                items = _apply_charity_ids(getItemsBySubCategory(category_id), charity_ids)
                paginated_items = self.paginator.paginate_queryset(items, request, self)
                serializer = ItemSerializer(paginated_items, many=True)
                response = self.paginator.get_paginated_response(serializer.data)
                disk.set(cache_key, response.data, ITEM_CATEGORY_TTL)
                return response
            else:
                cache_key = f'items_cat_{category_id}'
                if filter:
                    cache_key += f'_f_{filter}'
                if search_query:
                    cache_key += f'_s_{search_query}'
                cache_key += f'{charity_suffix}_p{page}'
                cached = disk.get(cache_key)
                if cached is not None:
                    return Response(cached)

                items = _apply_charity_ids(getItemsByFilter(category_id, filter, search_query), charity_ids)
                paginated_items = self.paginator.paginate_queryset(items, request, self)
                serializer = ItemSerializer(paginated_items, many=True)
                response = self.paginator.get_paginated_response(serializer.data)
                disk.set(cache_key, response.data, ITEM_CATEGORY_TTL)
                return response

        else:
            return Response("Please provide an item_id, search_text, category_id, or charity_id", status=400)
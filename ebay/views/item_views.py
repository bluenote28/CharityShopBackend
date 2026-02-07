from rest_framework.views import APIView
from rest_framework.response import Response
from ebay.models import Item
from ebay.serializers import ItemSerializer
from databasescripts.database_actions import retrieveItem, getItemsBySubCategory, getItemsByFilter
from rest_framework.pagination import PageNumberPagination

class EbayCharityItems(APIView):
    
    paginator = PageNumberPagination()
    paginator.page_size = 50 
    
    def get(self, request, item_id=None, search_text=None, category_id=None, filter=None):

        if item_id is not None:
            item = retrieveItem(item_id)
            if item is not None:
                serializer = ItemSerializer(item)
                return Response(serializer.data)
            else:
                return Response("Item not found", status=404)
            
        elif search_text is not None:
            items = Item.objects.filter(name__icontains=search_text)
            paginated_items = self.paginator.paginate_queryset(items, request, self)
            serializer = ItemSerializer(items, many=True)
            return self.paginator.get_paginated_response(serializer.data)
        
        elif category_id is not None:

           if filter is None: 
                items = getItemsBySubCategory(category_id)
                paginated_items = self.paginator.paginate_queryset(items, request, self)
                serializer = ItemSerializer(paginated_items, many=True)
                return self.paginator.get_paginated_response(serializer.data)
           else:
                items = getItemsByFilter(category_id, filter)
                paginated_items = self.paginator.paginate_queryset(items, request, self)
                serializer = ItemSerializer(paginated_items, many=True)
                return self.paginator.get_paginated_response(serializer.data)

        else:
            return Response("Please provide an item_id, search_text, or category_id", status=400)
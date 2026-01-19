from rest_framework.views import APIView
from rest_framework.response import Response
from ebay.models import Item
from ebay.serializers import ItemSerializer
from databasescripts.database_actions import retrieveItem, getItemsBySubCategory

class EbayCharityItems(APIView):
    
    def get(self, request, item_id=None, search_text=None, category_id=None):

        if item_id is not None:
            item = retrieveItem(item_id)
            if item is not None:
                serializer = ItemSerializer(item)
                return Response(serializer.data)
            else:
                return Response("Item not found", status=404)
            
        elif search_text is not None:
            items = Item.objects.filter(name__icontains=search_text)
            serializer = ItemSerializer(items, many=True)
            return Response(serializer.data)
        
        elif category_id is not None:
            items = getItemsBySubCategory(category_id)
            serializer = ItemSerializer(items, many=True)
            return Response(serializer.data)

        else:
            return Response("Please provide an item_id, search_text, or category_id", status=400)
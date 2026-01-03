from rest_framework.views import APIView
from rest_framework.response import Response
from ebay.models import Item
from ebay.serializers import ItemSerializer
from databasescripts.database_actions import retrieveItem

class EbayCharityItems(APIView):
    
    def get(self, request, item_id=None):

        if item_id is not None:
            item = retrieveItem(item_id)
            if item is not None:
                serializer = ItemSerializer(item)
                return Response(serializer.data)
            else:
                return Response("Item not found", status=404)

        else:

            items = Item.objects.all()
            serializer = ItemSerializer(items, many=True)
            return Response(serializer.data)
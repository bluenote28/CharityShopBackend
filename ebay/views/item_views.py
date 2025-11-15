from rest_framework.views import APIView
from rest_framework.response import Response
from ebay.models import Item
from ebay.serializers import ItemSerializer


class EbayCharityItems(APIView):
    
    def get(self, request):

        items = Item.objects.all()
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)
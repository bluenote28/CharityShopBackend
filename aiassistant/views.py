from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .ai_client import get_item_description

class AiItemAssistantView(APIView):

    def post(self, request):
        ebay_id = request.data.get('ebay_id')
        if not ebay_id:
            return Response({'detail': 'Missing eBay ID'}, status=status.HTTP_400_BAD_REQUEST)

        item_link = request.data.get('item_link') or f'https://www.ebay.com/itm/{ebay_id}'
        result = get_item_description(
            item_link,
            item_name=request.data.get('item_name'),
            ebay_id=ebay_id,
        )
        return Response(result)

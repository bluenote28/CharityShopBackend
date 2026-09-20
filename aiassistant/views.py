from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .ai_client import get_ai_advice

class AiItemAssistantView(APIView):

    def post(self, request):
        ebay_id = request.data.get('ebay_id')
        if not ebay_id:
            return Response({'detail': 'Missing eBay ID'}, status=status.HTTP_400_BAD_REQUEST)

        result = get_ai_advice(ebay_id)
        return Response(result)

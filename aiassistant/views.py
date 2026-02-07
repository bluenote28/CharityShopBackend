from rest_framework.views import APIView
from rest_framework.response import Response
from .bedrock_client import get_item_description

class AiItemAssistantView(APIView):

    def __init__(self):
        super().__init__()
    
    def post(self, request):
      
        item_name = request.data['item_name']

        response = get_item_description(item_name)

        return Response(response)
    
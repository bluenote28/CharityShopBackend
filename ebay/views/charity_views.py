from rest_framework.views import APIView
from rest_framework.response import Response
from ebay.serializers import CharitySerializer
from ebay.models import Charity

class EbayCharity(APIView):

    def __init__(self):
        super().__init__()

    def get(self, request):
        charities = Charity.objects.all()
        serializer = CharitySerializer(charities, many=True)
        
        return Response(serializer.data)
    
    def post(self, request):
        serializer = CharitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
    def delete(self, request, charity_id):
        charity = Charity.objects.get(id=charity_id)
        charity.delete()
        return Response(status=204)

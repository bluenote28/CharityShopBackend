from rest_framework.views import APIView
from rest_framework.response import Response
from ebay.serializers import CharitySerializer
from ebay.models import Charity
from databasescripts.database_actions import deleteCharity, addCharity

class EbayCharity(APIView):

    def __init__(self):
        super().__init__()

    def get(self, request):
        charities = Charity.objects.all()
        serializer = CharitySerializer(charities, many=True)
        
        return Response(serializer.data)
    
    def post(self, request):
        
        add = addCharity(request.data)
            
        if add == "Success": 
            return Response("Sucesfully added charity", status=201)
        else:
            return Response("Failed to add charity", status=400)
    
    def delete(self, request, charity_id):
        
        charity_delete = deleteCharity(charity_id)

        if charity_delete == "Success":
            return Response(status=204)
        else:
            return Response(charity_delete, status=500)

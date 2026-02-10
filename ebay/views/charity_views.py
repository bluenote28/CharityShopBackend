from rest_framework.views import APIView
from rest_framework.response import Response
from ebay.serializers import CharitySerializer
from ebay.models import Charity
from databasescripts.database_actions import deleteCharity, addCharity
from django.core.cache import caches

disk = caches['diskcache']
CHARITIES_CACHE_KEY = 'charities_list'
CHARITIES_CACHE_TTL = 60 * 60

class EbayCharity(APIView):

    def __init__(self):
        super().__init__()

    def get(self, request):
        cached = disk.get(CHARITIES_CACHE_KEY)
        if cached is not None:
            return Response(cached)

        charities = Charity.objects.all()
        serializer = CharitySerializer(charities, many=True)
        disk.set(CHARITIES_CACHE_KEY, serializer.data, CHARITIES_CACHE_TTL)
        return Response(serializer.data)

    def post(self, request):

        add = addCharity(request.data)

        if add == "Success":
            disk.delete(CHARITIES_CACHE_KEY)
            return Response("Sucesfully added charity", status=201)
        else:
            return Response("Failed to add charity", status=400)

    def delete(self, request, charity_id):

        charity_delete = deleteCharity(charity_id)

        if charity_delete == "Success":
            disk.delete(CHARITIES_CACHE_KEY)
            return Response(status=204)
        else:
            return Response(charity_delete, status=500)

    def put(self, request, charity_id):

        try:
            charity = Charity.objects.get(id=charity_id)
            charity.id = charity_id
            charity.name = request.data['name']
            charity.description = request.data['description']
            charity.donation_url = request.data['donation_url']
            charity.image_url = request.data['image_url']

            charity.save()
            disk.delete(CHARITIES_CACHE_KEY)
            return Response(status=204)

        except Exception as e:
            return Response(f"{e}", status=500)
            





        

        



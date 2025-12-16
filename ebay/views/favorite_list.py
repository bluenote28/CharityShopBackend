from rest_framework.views import APIView
from rest_framework.response import Response
from ebay.models import FavoriteList, Item, User
from ebay.serializers import FavoriteListSerializer, CharitySerializer, ItemSerializer

class FavoriteListView(APIView):
    
    def get(self, request):
        user = User.objects.get(username=request.user)
        favorite_list = FavoriteList.objects.get(user=user.id)
        serializer = FavoriteListSerializer(favorite_list, many=False)
        return Response(serializer.data)
    
    def post(self, request):
        data = request.data  
        favorite_list = FavoriteList.objects.get(user=request.user)

        if data['item'] != "":
            item = Item.objects.get(ebay_id=data['item'])
            favorite_list.items.add(item)

        if data['charity']!= "":
            charity_serializer = CharitySerializer(data=data['charity'])
            if charity_serializer.is_valid():
                favorite_list.charities.add(data['charity'])

        favorite_list.save()
        serializer = FavoriteListSerializer(favorite_list, many=False)

        return Response(serializer.data)
    
    def delete(self, request):
        user = request.user
        data = request.data
        
        favorite_list = FavoriteList.objects.get(user=user)

        if 'item' in data:
            item = Item.objects.get(ebay_id=data['item'])
            favorite_list.items.remove(item)

        if 'charity' in data:
            favorite_list.charities.remove(data['charity'])

        favorite_list.save()
        serializer = FavoriteListSerializer(favorite_list, many=False)
        return Response(serializer.data)

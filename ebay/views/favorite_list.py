from rest_framework.views import APIView
from rest_framework.response import Response
from ebay.models import FavoriteList, Item, User
from ebay.serializers import FavoriteListSerializer

class FavoriteListView(APIView):

    def _favorite_field(self, request, field):
        data = request.data or {}
        value = data.get(field)
        if value in (None, ''):
            value = request.query_params.get(field)
        return value or None

    def _charity_id(self, value):
        if isinstance(value, dict):
            return value.get('id')
        return value
    
    def get(self, request):
        user = User.objects.get(username=request.user)
        favorite_list = FavoriteList.objects.prefetch_related('items', 'charities').get(user=user.id)
        serializer = FavoriteListSerializer(favorite_list, many=False)
        return Response(serializer.data)
    
    def post(self, request):
        favorite_list = FavoriteList.objects.prefetch_related('items', 'charities').get(user=request.user)
        item_id = self._favorite_field(request, 'item')
        charity_id = self._charity_id(self._favorite_field(request, 'charity'))

        if item_id:
            item = Item.objects.get(ebay_id=item_id)
            favorite_list.items.add(item)

        if charity_id:
            favorite_list.charities.add(charity_id)

        favorite_list.save()
        serializer = FavoriteListSerializer(favorite_list, many=False)

        return Response(serializer.data)
    
    def delete(self, request):
        user = request.user
        item_id = self._favorite_field(request, 'item')
        charity_id = self._favorite_field(request, 'charity')
        
        favorite_list = FavoriteList.objects.prefetch_related('items', 'charities').get(user=user)

        if item_id:
            item = Item.objects.get(ebay_id=item_id)
            favorite_list.items.remove(item)

        if charity_id:
            favorite_list.charities.remove(charity_id)

        favorite_list.save()
        serializer = FavoriteListSerializer(favorite_list, many=False)
        return Response(serializer.data)

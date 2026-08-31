from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from ebay.models import Purchase
from ebay.serializers import PurchaseSerializer


class PurchaseView(APIView):
    permission_classes = [IsAuthenticated]

    def _purchases_for_user(self, user_id):
        return (
            Purchase.objects
            .filter(user_id=user_id)
            .select_related('charity')
            .order_by('-purchased_at', '-created_at')
        )

    def get(self, request, user_id=None):
        person_id = user_id if user_id is not None else request.user.id
        serializer = PurchaseSerializer(self._purchases_for_user(person_id), many=True)
        return Response(serializer.data)

    def post(self, request, user_id=None):
        serializer = PurchaseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(user=request.user)
        purchases = PurchaseSerializer(self._purchases_for_user(request.user.id), many=True)
        return Response(purchases.data, status=status.HTTP_201_CREATED)

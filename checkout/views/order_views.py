from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from checkout.models import CheckoutSession, PurchaseOrder
from checkout.serializers import PurchaseOrderSerializer
from checkout.checkout_client import CheckoutClient
import logging

logger = logging.getLogger(__name__)


class PlaceOrderView(APIView):

    def post(self, request, session_id):
        client = CheckoutClient()
        result = client.place_order(session_id)

        if 'error' in result:
            return Response(result, status=status.HTTP_502_BAD_GATEWAY)

        try:
            checkout_session = CheckoutSession.objects.get(ebay_session_id=session_id)
            checkout_session.status = 'COMPLETED'
            checkout_session.save()

            purchase_order = PurchaseOrder.objects.create(
                ebay_order_id=result.get('purchaseOrderId', ''),
                checkout_session=checkout_session,
                ebay_response=result,
                order_total=checkout_session.total,
                currency=checkout_session.currency,
                status='CONFIRMED',
            )

            serializer = PurchaseOrderSerializer(purchase_order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except CheckoutSession.DoesNotExist:
            logger.warning(f"Placed order for session {session_id} but no local record found")
            return Response(result, status=status.HTTP_201_CREATED)


class PurchaseOrderDetailView(APIView):

    def get(self, request, order_id):
        client = CheckoutClient()
        result = client.get_purchase_order(order_id)

        if 'error' in result:
            return Response(result, status=status.HTTP_502_BAD_GATEWAY)

        try:
            purchase_order = PurchaseOrder.objects.get(ebay_order_id=order_id)
            purchase_order.ebay_response = result
            purchase_order.save()
        except PurchaseOrder.DoesNotExist:
            pass

        return Response(result)

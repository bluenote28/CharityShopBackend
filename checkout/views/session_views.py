from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from checkout.models import CheckoutSession
from checkout.serializers import (
    CheckoutSessionSerializer,
    InitiateCheckoutSerializer,
    UpdateQuantitySerializer,
    UpdateShippingOptionSerializer,
    ApplyCouponSerializer,
)
from checkout.checkout_client import CheckoutClient
from ebay.models import Item
import logging

logger = logging.getLogger(__name__)


class InitiateCheckoutView(APIView):

    def post(self, request):
        serializer = InitiateCheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        ebay_payload = {
            "contactEmail": data['buyer_email'],
            "lineItemInputs": [
                {
                    "itemId": data['item_id'],
                    "quantity": data['quantity'],
                }
            ],
            "shippingAddress": {
                "recipient": f"{data['recipient_first_name']} {data['recipient_last_name']}",
                "phoneNumber": data.get('phone_number', ''),
                "addressLine1": data['address_line1'],
                "addressLine2": data.get('address_line2', ''),
                "city": data['city'],
                "stateOrProvince": data['state_or_province'],
                "postalCode": data['postal_code'],
                "country": data['country'],
            }
        }

        client = CheckoutClient()
        result = client.initiate_checkout(ebay_payload)

        if 'error' in result:
            return Response(result, status=status.HTTP_502_BAD_GATEWAY)

        shipping_address = {
            "recipient_first_name": data['recipient_first_name'],
            "recipient_last_name": data['recipient_last_name'],
            "address_line1": data['address_line1'],
            "address_line2": data.get('address_line2', ''),
            "city": data['city'],
            "state_or_province": data['state_or_province'],
            "postal_code": data['postal_code'],
            "country": data['country'],
        }

        pricing = result.get('pricingSummary', {})

        checkout_session = CheckoutSession.objects.create(
            ebay_session_id=result['checkoutSessionId'],
            buyer_email=data['buyer_email'],
            shipping_address=shipping_address,
            ebay_response=result,
            subtotal=pricing.get('priceSubtotal', {}).get('value'),
            shipping_cost=pricing.get('deliveryCost', {}).get('value'),
            tax=pricing.get('tax', {}).get('value'),
            total=pricing.get('total', {}).get('value'),
            currency=pricing.get('total', {}).get('currency', 'USD'),
            status='CREATED',
        )

        try:
            item = Item.objects.get(ebay_id=data['item_id'])
            checkout_session.items.add(item)
        except Item.DoesNotExist:
            pass

        session_serializer = CheckoutSessionSerializer(checkout_session)
        return Response(session_serializer.data, status=status.HTTP_201_CREATED)


class CheckoutSessionDetailView(APIView):

    def get(self, request, session_id):
        client = CheckoutClient()
        result = client.get_checkout_session(session_id)

        if 'error' in result:
            return Response(result, status=status.HTTP_502_BAD_GATEWAY)

        try:
            checkout_session = CheckoutSession.objects.get(ebay_session_id=session_id)
            checkout_session.ebay_response = result
            pricing = result.get('pricingSummary', {})
            checkout_session.subtotal = pricing.get('priceSubtotal', {}).get('value')
            checkout_session.shipping_cost = pricing.get('deliveryCost', {}).get('value')
            checkout_session.tax = pricing.get('tax', {}).get('value')
            checkout_session.total = pricing.get('total', {}).get('value')
            checkout_session.save()
        except CheckoutSession.DoesNotExist:
            pass

        return Response(result)


class UpdateQuantityView(APIView):

    def post(self, request, session_id):
        serializer = UpdateQuantitySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        ebay_payload = {
            "lineItemId": data['line_item_id'],
            "quantity": data['quantity'],
        }

        client = CheckoutClient()
        result = client.update_quantity(session_id, ebay_payload)

        if 'error' in result:
            return Response(result, status=status.HTTP_502_BAD_GATEWAY)

        try:
            session = CheckoutSession.objects.get(ebay_session_id=session_id)
            session.ebay_response = result
            session.status = 'UPDATED'
            pricing = result.get('pricingSummary', {})
            session.total = pricing.get('total', {}).get('value')
            session.save()
        except CheckoutSession.DoesNotExist:
            pass

        return Response(result)


class UpdateShippingOptionView(APIView):

    def post(self, request, session_id):
        serializer = UpdateShippingOptionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        ebay_payload = {
            "lineItemId": data['line_item_id'],
            "shippingOptionId": data['shipping_option_id'],
        }

        client = CheckoutClient()
        result = client.update_shipping_option(session_id, ebay_payload)

        if 'error' in result:
            return Response(result, status=status.HTTP_502_BAD_GATEWAY)

        try:
            session = CheckoutSession.objects.get(ebay_session_id=session_id)
            session.ebay_response = result
            session.status = 'UPDATED'
            session.save()
        except CheckoutSession.DoesNotExist:
            pass

        return Response(result)


class ApplyCouponView(APIView):

    def post(self, request, session_id):
        serializer = ApplyCouponSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        ebay_payload = {
            "redemptionCode": data['redemption_code'],
        }

        client = CheckoutClient()
        result = client.apply_coupon(session_id, ebay_payload)

        if 'error' in result:
            return Response(result, status=status.HTTP_502_BAD_GATEWAY)

        return Response(result)

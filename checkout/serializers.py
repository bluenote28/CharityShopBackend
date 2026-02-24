from rest_framework import serializers
from .models import CheckoutSession, PurchaseOrder


class CheckoutSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckoutSession
        fields = '__all__'


class PurchaseOrderSerializer(serializers.ModelSerializer):
    checkout_session = CheckoutSessionSerializer(read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = '__all__'


class InitiateCheckoutSerializer(serializers.Serializer):
    buyer_email = serializers.EmailField()
    item_id = serializers.CharField(max_length=100)
    quantity = serializers.IntegerField(min_value=1, default=1)

    recipient_first_name = serializers.CharField(max_length=100)
    recipient_last_name = serializers.CharField(max_length=100)
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    state_or_province = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=2, default='US')
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)


class UpdateQuantitySerializer(serializers.Serializer):
    line_item_id = serializers.CharField(max_length=255)
    quantity = serializers.IntegerField(min_value=1)


class UpdateShippingOptionSerializer(serializers.Serializer):
    line_item_id = serializers.CharField(max_length=255)
    shipping_option_id = serializers.CharField(max_length=255)


class ApplyCouponSerializer(serializers.Serializer):
    redemption_code = serializers.CharField(max_length=255)

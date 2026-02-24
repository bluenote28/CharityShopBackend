from django.urls import path
from checkout.views.session_views import (
    InitiateCheckoutView,
    CheckoutSessionDetailView,
    UpdateQuantityView,
    UpdateShippingOptionView,
    ApplyCouponView,
)

urlpatterns = [
    path('initiate/', InitiateCheckoutView.as_view(), name='checkout-initiate'),
    path('<str:session_id>/', CheckoutSessionDetailView.as_view(), name='checkout-session-detail'),
    path('<str:session_id>/update_quantity/', UpdateQuantityView.as_view(), name='checkout-update-quantity'),
    path('<str:session_id>/update_shipping/', UpdateShippingOptionView.as_view(), name='checkout-update-shipping'),
    path('<str:session_id>/apply_coupon/', ApplyCouponView.as_view(), name='checkout-apply-coupon'),
]

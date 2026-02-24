from django.urls import path
from checkout.views.order_views import PlaceOrderView, PurchaseOrderDetailView

urlpatterns = [
    path('place/<str:session_id>/', PlaceOrderView.as_view(), name='checkout-place-order'),
    path('<str:order_id>/', PurchaseOrderDetailView.as_view(), name='purchase-order-detail'),
]

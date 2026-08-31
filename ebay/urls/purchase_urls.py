from django.urls import path
from ebay.views.purchase_views import PurchaseView

urlpatterns = [
    path('', PurchaseView.as_view()),
    path('<int:user_id>/', PurchaseView.as_view()),
]

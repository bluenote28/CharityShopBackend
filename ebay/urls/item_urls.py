from django.urls import path
from ebay.views.item_views import EbayCharityItems


urlpatterns = [
    path('ebaycharityitems/', EbayCharityItems.as_view()),
    path('ebaycharityitems/<str:item_id>', EbayCharityItems.as_view()),
]
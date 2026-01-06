from django.urls import path
from ebay.views.item_views import EbayCharityItems


urlpatterns = [
    path('ebaycharityitems/<str:item_id>', EbayCharityItems.as_view()),
    path('ebaycharityitems/search/<str:search_text>', EbayCharityItems.as_view()),
    path('ebaycharityitems/category/<str:category_id>', EbayCharityItems.as_view()),
]
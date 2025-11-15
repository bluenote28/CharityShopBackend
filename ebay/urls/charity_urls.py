from django.urls import path
from ebay.views.charity_views import EbayCharity

urlpatterns = [
    path('getCharities/', EbayCharity.as_view()),
    path('addCharity/', EbayCharity.as_view()),
    path('deleteCharity/<int:charity_id>', EbayCharity.as_view()),
    path('updateCharity/<int:charity_id>', EbayCharity.as_view()),
]
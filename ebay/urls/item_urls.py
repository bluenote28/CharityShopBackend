from django.urls import path, register_converter
from ebay.views.item_views import EbayCharityItems

class CategoryWithSlashConverter:
    regex = "[a-zA-ZÀ-ÿ,& /'-]+"

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return value.replace('/', '%2F')

register_converter(CategoryWithSlashConverter, "cat")

urlpatterns = [
    path('ebaycharityitems/<str:item_id>', EbayCharityItems.as_view()),
    path('ebaycharityitems/search/<str:search_text>', EbayCharityItems.as_view()),
    path('ebaycharityitems/category/<cat:category_id>/<str:filter>', EbayCharityItems.as_view()),
    path('ebaycharityitems/category/<cat:category_id>', EbayCharityItems.as_view()),
]

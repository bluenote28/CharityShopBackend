from rest_framework.views import APIView
from rest_framework.response import Response
from ebay.models import Item
from ebay.models import Charity
from rest_framework.permissions import IsAdminUser


class EbayReportView(APIView):
    def __init__(self):
        super().__init__()

    permission_classes = [IsAdminUser]

    def get(self, request):
        total_items = Item.objects.count()
        total_charities = Charity.objects.count()

        all_charities = Charity.objects.all()
        items_per_charity = {}

        for charity in all_charities:
            item_count = Item.objects.filter(charity=charity).count()
            items_per_charity[charity.name] = item_count
        
        report_data = {
            'total_items': total_items,
            'total_charities': total_charities,
            'items_per_charity': items_per_charity
        }
        
        return Response(report_data)
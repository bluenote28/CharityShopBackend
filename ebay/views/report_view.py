from rest_framework.views import APIView
from rest_framework.response import Response
from ebay.models import Item
from ebay.models import Charity
from rest_framework.permissions import IsAdminUser
from django.core.cache import caches

disk = caches['diskcache']
REPORT_CACHE_KEY = 'report_data'
REPORT_CACHE_TTL = 60 * 30


class EbayReportView(APIView):
    def __init__(self):
        super().__init__()

    permission_classes = [IsAdminUser]

    def get(self, request):
        cached = disk.get(REPORT_CACHE_KEY)
        if cached is not None:
            return Response(cached)

        total_items = Item.objects.count()
        total_charities = Charity.objects.count()

        all_charities = Charity.objects.all()
        items_per_charity = []

        for charity in all_charities:
            item_count = Item.objects.filter(charity=charity).count()
            items_per_charity.append({"name": charity.name, "item_count": item_count})

        report_data = {
            'total_items': total_items,
            'total_charities': total_charities,
            'items_per_charity': items_per_charity
        }

        disk.set(REPORT_CACHE_KEY, report_data, REPORT_CACHE_TTL)
        return Response(report_data)
from django.urls import path
from ebay.views.report_view import EbayReportView


urlpatterns = [
    path('report/', EbayReportView.as_view()),
]
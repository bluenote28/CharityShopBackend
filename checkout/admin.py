from django.contrib import admin
from .models import CheckoutSession, PurchaseOrder

admin.site.register(CheckoutSession)
admin.site.register(PurchaseOrder)

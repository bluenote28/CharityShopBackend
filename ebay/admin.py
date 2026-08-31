from django.contrib import admin
from .models import Charity, Item, FavoriteList, Purchase

admin.site.register(Charity)
admin.site.register(Item)
admin.site.register(FavoriteList)
admin.site.register(Purchase)
from django.contrib import admin
from .models import Charity, Item, FavoriteList

admin.site.register(Charity)
admin.site.register(Item)
admin.site.register(FavoriteList)
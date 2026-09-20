from django.contrib import admin
from django.urls import path, include
from ebay.views.favorite_list import FavoriteListView
from databasescripts.views import RefreshDatabaseView
from aiassistant.views import AiItemAssistantView, AiChatView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/charity/', include('ebay.urls.charity_urls')),
    path('api/items/', include('ebay.urls.item_urls')),
    path('api/users/', include('ebay.urls.user_urls')),
    path('api/report/', include('ebay.urls.report_urls')),
    path('api/purchases/', include('ebay.urls.purchase_urls')),
    path('api/favorites/', FavoriteListView.as_view()),
    path('api/ai_assistant/chat/', AiChatView.as_view()),
    path('api/ai_assistant/', AiItemAssistantView.as_view()),
    path('api/refresh_items/', RefreshDatabaseView.as_view()),
    path('accounts/', include('allauth.urls')),
]

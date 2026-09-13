from django.urls import path
from ebay.views.user_views import GetUserProfile, GetUsers, GoogleLogin


urlpatterns = [
    path('google/', GoogleLogin.as_view(), name='google-login'),
    path('profile/', GetUserProfile.as_view(), name='users-profile'),
    path('profile/update/', GetUserProfile.as_view(), name='users-profile-update'),
    path('getUsers/', GetUsers.as_view(), name='users')
]

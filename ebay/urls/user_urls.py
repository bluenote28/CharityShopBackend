from django.urls import path
from ebay.views.user_views import GetUserProfile, GetUsers, RegisterUser, MyTokenObtainPairView


urlpatterns = [
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', RegisterUser.as_view(), name='register'),
    path('profile/', GetUserProfile.as_view(), name='users-profile'),
    path('profile/update/', GetUserProfile.as_view(), name='users-profile-update'),
    path('getUsers/', GetUsers.as_view(), name='users')
]
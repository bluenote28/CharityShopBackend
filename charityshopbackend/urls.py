from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/charity/', include('ebay.urls.charity_urls')),
    path('api/items/', include('ebay.urls.item_urls')),
    path('api/users/', include('ebay.urls.user_urls')),
    path('api/report/', include('ebay.urls.report_urls')),
    path("password_reset/", auth_views.PasswordResetView.as_view(template_name='reset_password.html'), name="reset_password.html"),
    path("reset_password_sent/", auth_views.PasswordResetDoneView.as_view(template_name='reset_password_sent.html'), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name='reset.html'), name="password_reset_confirm"),
    path("reset_password_complete/", auth_views.PasswordResetCompleteView.as_view(template_name='reset_password_complete.html'), name='password_reset_complete')
]

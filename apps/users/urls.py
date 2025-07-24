from django.urls import path
from .views import register_user, logout_user, custom_token_obtain_pair
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("register/", register_user, name="register"),
    path("login/", custom_token_obtain_pair.as_view(), name="token_obtain_pair"), 
    path("logout/", logout_user, name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),   
]

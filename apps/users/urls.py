from django.urls import path
from .views import RegisterUserView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,    
    TokenRefreshView,      
    TokenVerifyView,       
    TokenBlacklistView,      
)

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register"),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('token/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
]

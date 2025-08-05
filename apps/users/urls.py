from django.urls import path, include
from .views import RegisterUserView, ForgotPasswordView, ResetPasswordView, CustomTokenObtainPairView, UnlockUserView, GoogleLogin, GithubLogin
from rest_framework_simplejwt.views import (    
    TokenRefreshView,      
    TokenVerifyView,       
    TokenBlacklistView,      
)

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="api-register"),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('token/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', ResetPasswordView.as_view(), name='reset_password'),
    path("unlock-user/", UnlockUserView.as_view(), name="unlock_user"),

    path("social-login/google/", GoogleLogin.as_view(), name="google_login"),
    path("social-login/github/", GithubLogin.as_view(), name="github_login"),
]

from django.urls import path
from .views import RegisterUserView, LogoutUserView, CustomTokenObtainPairView
from .views_ui import LoginView, LogoutView, RegisterView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # API endpoints JWT
    path("register/", RegisterUserView.as_view(), name="register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("logout/", LogoutUserView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

from django.urls import path, include
from .views_ui import LoginView, LogoutView, RegisterView


from django.views.generic import RedirectView
urlpatterns = [
    path("", RedirectView.as_view(url="/blog/", permanent=False)),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
]

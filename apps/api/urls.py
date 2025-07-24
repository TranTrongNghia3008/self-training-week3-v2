from django.urls import path, include
from .views import protected_view

urlpatterns = [
    path("protected/", protected_view, name="protected_view"),
    path("users/", include("apps.users.urls")), 
]

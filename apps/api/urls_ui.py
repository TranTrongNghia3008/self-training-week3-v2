from django.urls import path, include

urlpatterns = [
    path("", include("apps.users.urls_ui")),      
    path("blog/", include("apps.blog.urls_ui")),  
]
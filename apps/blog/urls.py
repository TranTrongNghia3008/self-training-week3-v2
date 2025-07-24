# apps/blog/urls.py

from django.urls import path
from .views import (
    PostListCreateAPIView,
    PostRetrieveUpdateDestroyAPIView,
    CommentListCreateAPIView,
    CategoryListAPIView,
)

urlpatterns = [
    path("posts/", PostListCreateAPIView.as_view(), name="post-list-create"),
    path("posts/<int:pk>/", PostRetrieveUpdateDestroyAPIView.as_view(), name="post-detail"),
    path("posts/<int:post_id>/comments/", CommentListCreateAPIView.as_view(), name="post-comments"),
    path("categories/", CategoryListAPIView.as_view(), name="category-list"),
]

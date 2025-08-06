from django.urls import path
from .views import (
    PostListCreateAPIView,
    PostRetrieveUpdateDestroyAPIView,
    CommentListCreateAPIView,
    CommentRetrieveUpdateDestroyAPIView,
    CategoryListCreateAPIView,
    MediaListCreateAPIView,
    MediaRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path("posts/", PostListCreateAPIView.as_view(), name="post-list-create"),
    path("posts/<int:pk>/", PostRetrieveUpdateDestroyAPIView.as_view(), name="post-detail"),
    path("posts/<int:post_id>/comments/", CommentListCreateAPIView.as_view(), name="post-comments"),
    path("comments/<int:pk>/", CommentRetrieveUpdateDestroyAPIView.as_view(), name="comment-detail"),
    path("categories/", CategoryListCreateAPIView.as_view(), name="category-list"),
    path("categories/<int:pk>/", CategoryListCreateAPIView.as_view(), name="category-list-create"),
    path("media/", MediaListCreateAPIView.as_view(), name="media-list-create"),
    path("media/<int:pk>/", MediaRetrieveUpdateDestroyAPIView.as_view(), name="media-detail"),
]

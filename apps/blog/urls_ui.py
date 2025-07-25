from django.urls import path
from .views_ui import (
    PostListView, PostDetailView, PostCreateView,
    PostUpdateView, PostDeleteView, CommentCreateView,
)

app_name = "blog_ui"

urlpatterns = [
    path("", PostListView.as_view(), name="post-list-html"),
    path("posts/create/", PostCreateView.as_view(), name="post-create-html"),
    path("posts/<int:pk>/", PostDetailView.as_view(), name="post-detail-html"),
    path("posts/<int:pk>/edit/", PostUpdateView.as_view(), name="post-edit-html"),
    path("posts/<int:pk>/delete/", PostDeleteView.as_view(), name="post-delete-html"),
    path("posts/<int:post_id>/comment/", CommentCreateView.as_view(), name="post-comment-html"),
]

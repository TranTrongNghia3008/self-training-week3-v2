from django.urls import path
from .views import (
    PostListCreateAPIView,
    PostRetrieveUpdateDestroyAPIView,
    RelatedPostsAPIView,
    CommentListCreateAPIView,
    CommentRetrieveUpdateDestroyAPIView,
    CategoryListCreateAPIView,
    MediaListCreateAPIView,
    MediaRetrieveUpdateDestroyAPIView,
    CategoryReportAPIView,
    SearchAnalyticsAPIView,
    SearchClickUpdateAPIView
)

urlpatterns = [
    path("posts/", PostListCreateAPIView.as_view(), name="post-list-create"),
    path("posts/<int:pk>/", PostRetrieveUpdateDestroyAPIView.as_view(), name="post-detail"),
    path("posts/<int:post_id>/related/", RelatedPostsAPIView.as_view(), name="post-related"),

    path("posts/<int:post_id>/comments/", CommentListCreateAPIView.as_view(), name="post-comments"),
    path("comments/<int:pk>/", CommentRetrieveUpdateDestroyAPIView.as_view(), name="comment-detail"),

    path("categories/", CategoryListCreateAPIView.as_view(), name="category-list"),
    path("categories/<int:pk>/", CategoryListCreateAPIView.as_view(), 
    name="category-list-create"),
    path('categories/report/', CategoryReportAPIView.as_view(), name='category-report'),

    path("media/", MediaListCreateAPIView.as_view(), name="media-list-create"),
    path("media/<int:pk>/", MediaRetrieveUpdateDestroyAPIView.as_view(), name="media-detail"),

    path('analytics/search/', SearchAnalyticsAPIView.as_view(), name='search-analytics'),
    path('analytics/search/click/', SearchClickUpdateAPIView.as_view(), name='search-click-update'),
]

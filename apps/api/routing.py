from django.urls import re_path
from apps.blog.consumers import CommentConsumer
from apps.notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    re_path(r"ws/posts/(?P<post_id>\d+)/$", CommentConsumer.as_asgi()),
    re_path(r"ws/notifications/(?P<user_id>\d+)/$", NotificationConsumer.as_asgi()),
]

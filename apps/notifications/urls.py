from django.urls import path
from .views import (
    NotificationListAPIView,
    MarkNotificationAsReadAPIView,
    MarkAllNotificationsAsReadAPIView,
    DeleteNotificationAPIView,
    DeleteAllNotificationsAPIView,
)

urlpatterns = [
    path("", NotificationListAPIView.as_view(), name="notification-list"),
    path("<int:pk>/read/", MarkNotificationAsReadAPIView.as_view(), name="notification-mark-read"),
    path("read-all/", MarkAllNotificationsAsReadAPIView.as_view(), name="notification-read-all"),
    path("<int:pk>/delete/", DeleteNotificationAPIView.as_view(), name="notification-delete"),
    path("delete-all/", DeleteAllNotificationsAPIView.as_view(), name="notification-delete-all"),
]

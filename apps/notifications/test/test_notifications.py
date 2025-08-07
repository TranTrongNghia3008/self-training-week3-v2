from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models.signals import post_save
from apps.notifications.signals import send_realtime_notification
from apps.notifications.models import Notification
from apps.notifications.test.factories import UserFactory, NotificationFactory

class NotificationAPITestCase(APITestCase):
    def setUp(self):
        post_save.disconnect(send_realtime_notification, sender=Notification)
        self.user = UserFactory(username="test-notification-user")

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.auth_header = {'HTTP_AUTHORIZATION': f'Bearer {self.access_token}'}

        # Notifications của self.user
        self.notification1 = NotificationFactory(recipient=self.user)
        self.notification2 = NotificationFactory(recipient=self.user)
        self.notification3 = NotificationFactory(recipient=self.user, is_read=True)

    def tearDown(self):
        post_save.connect(send_realtime_notification, sender=Notification)

    def test_list_notifications(self):
        url = reverse('notifications:notification-list')
        response = self.client.get(url, user=self.user, **self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_mark_single_notification_as_read(self):
        url = reverse('notifications:notification-mark-read', kwargs={'pk': self.notification1.pk})
        response = self.client.post(url, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)

    def test_mark_all_notifications_as_read(self):
        url = reverse('notifications:notification-read-all')
        response = self.client.post(url, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        unread_count = Notification.objects.filter(recipient=self.user, is_read=False).count()
        self.assertEqual(unread_count, 0)

    def test_delete_single_notification(self):
        url = reverse('notifications:notification-delete', kwargs={'pk': self.notification2.pk})
        response = self.client.delete(url, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        exists = Notification.objects.filter(pk=self.notification2.pk).exists()
        self.assertFalse(exists)

    def test_delete_all_notifications(self):
        url = reverse('notifications:notification-delete-all')
        response = self.client.delete(url, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        total = Notification.objects.filter(recipient=self.user).count()
        self.assertEqual(total, 0)

    def test_cannot_access_other_user_notification(self):
        other_user = UserFactory()
        other_notification = NotificationFactory(recipient=other_user)

        url = reverse('notifications:notification-delete', kwargs={'pk': other_notification.pk})
        response = self.client.delete(url, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url = reverse('notifications:notification-mark-read', kwargs={'pk': other_notification.pk})
        response = self.client.post(url, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

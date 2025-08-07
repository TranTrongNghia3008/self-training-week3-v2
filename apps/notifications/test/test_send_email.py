from django.test import TestCase
from apps.notifications.tasks import send_notification_email

class NotificationTests(TestCase):
    def test_send_email(self):
        result = send_notification_email.delay(
            "Test Subject", "Test Body", "nghia.trantrong3008@gmail.com"
        )
        self.assertTrue(result.id is not None)

    def test_send_notification_email_sync(self):
        result = send_notification_email.delay(
            subject="Test",
            message="This is a test",
            recipient_email="test@example.com"
        )
        self.assertIsNone(result.result) 


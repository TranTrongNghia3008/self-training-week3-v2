from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache

from apps.users.test.factories import UserFactory  
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthTests(APITestCase):

    def setUp(self):
        cache.clear()
        self.password = "testpass123"
        self.user = UserFactory(password=self.password)
        self.email = self.user.email

        self.register_url = reverse("api-register")
        self.login_url = reverse("token_obtain_pair")
        self.refresh_url = reverse("token_refresh")
        self.blacklist_url = reverse("token_blacklist")
        self.forgot_password_url = reverse("forgot_password")
        self.reset_password_url = lambda uidb64, token: reverse(
            "reset_password", kwargs={"uidb64": uidb64, "token": token}
        )
        self.unlock_url = reverse("unlock_user")

    def test_register_user(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpass123"
        }

        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("username", response.data)
        self.assertEqual(response.data["username"], "newuser")

    def test_login_user(self):
        data = {
            "username": self.user.username,
            "password": self.password
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_invalid_login_wrong_password(self):
        data = {
            "email": self.email,
            "password": "wrongpass"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_login_nonexistent_user(self):
        data = {
            "email": "notfound@example.com",
            "password": "any"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post(self.refresh_url, {"refresh": str(refresh)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_logout_blacklist_token(self):
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post(self.blacklist_url, {"refresh": str(refresh)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("apps.notifications.tasks.send_notification_email.delay")
    def test_forgot_password(self, mock_send_email):
        response = self.client.post(self.forgot_password_url, {"email": self.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_email.assert_called_once()

    def test_reset_password(self):
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = self.reset_password_url(uidb64, token)
        new_password = "newsecurepass"
        response = self.client.post(url, {"password": new_password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))

    @patch("apps.notifications.tasks.send_notification_email.delay")
    @patch("apps.users.views.LoginRateThrottle.allow_request", return_value=True)
    def test_account_locked_after_failed_attempts(self, mock_throttle, mock_send_email):
        user = UserFactory(password=self.password)
        for _ in range(5):
            response = self.client.post(self.login_url, {"username": user.username, "password": "wrongpass"})
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(self.login_url, {"username": user.username, "password": "wrongpass"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "This account is locked.")

        user.refresh_from_db()
        self.assertTrue(user.is_locked)

        mock_send_email.assert_called_once_with(
            subject="Your account has been locked",
            message="You have entered the wrong password too many times. Please contact admin.",
            recipient_email=user.email
        )

    def test_unlock_user_by_admin(self):
        locked_user = UserFactory(is_locked=True, failed_login_attempts=5)
        admin_user = UserFactory(is_staff=True, is_superuser=True)

        # Authenticate as admin
        refresh = RefreshToken.for_user(admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        # Unlock the user
        response = self.client.post(self.unlock_url, {"username": locked_user.username})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("has been unlocked", response.data["detail"])

        # Check DB
        locked_user.refresh_from_db()
        self.assertFalse(locked_user.is_locked)
        self.assertEqual(locked_user.failed_login_attempts, 0)


from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

from apps.users.test.factories import UserFactory  
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthTests(APITestCase):

    def setUp(self):
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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_login_nonexistent_user(self):
        data = {
            "email": "notfound@example.com",
            "password": "any"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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

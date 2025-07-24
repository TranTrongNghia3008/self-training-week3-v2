# apps/users/tests/test_auth.py

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

import datetime
from unittest.mock import patch

User = get_user_model()


class AuthTests(APITestCase):

    def setUp(self):
        self.register_url = reverse("register")
        self.login_url = reverse("token_obtain_pair")  # custom_token_obtain_pair
        self.logout_url = reverse("logout")
        self.protected_url = "/api/protected/"
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "strongpassword123"
        }
        self.user = User.objects.create_user(**self.user_data)

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

    def test_login_user_returns_tokens(self):
        data = {
            "username": self.user_data["username"],
            "password": self.user_data["password"]
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_logout_user_blacklists_token(self):
        # Login để lấy token
        login_response = self.client.post(self.login_url, {
            "username": self.user_data["username"],
            "password": self.user_data["password"]
        })
        refresh_token = login_response.data["refresh"]

        # Gửi token tới logout
        response = self.client.post(self.logout_url, {"refresh": refresh_token})
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(response.data["message"], "Logout successful")

    # def test_access_protected_after_logout(self):
    #     # Đăng nhập lấy token
    #     login = self.client.post(self.login_url, {
    #         "username": self.user_data["username"],
    #         "password": self.user_data["password"]
    #     })
    #     access = login.data["access"]
    #     refresh = login.data["refresh"]

    #     print(f"Access Token: {access}")
    #     print(f"Refresh Token: {refresh}")

    #     # Logout (blacklist refresh token)
    #     self.client.post(self.logout_url, {"refresh": refresh})

    #     print("After logout, trying to access protected view...")

    #     # Gửi request với access token cũ
    #     self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    #     print("Accessing protected view...")

    #     response = self.client.get(self.protected_url)

    #     print(f"Response: {response}")

    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # @patch("rest_framework_simplejwt.tokens.datetime")
    # def test_access_token_expired(self, mock_datetime):
    #     # Đăng nhập lấy token
    #     login = self.client.post(self.login_url, {
    #         "username": self.user_data["username"],
    #         "password": self.user_data["password"]
    #     })
    #     access = login.data["access"]

    #     # Giả lập token hết hạn bằng cách giả lập thời gian tương lai
    #     future = datetime.datetime.utcnow() + datetime.timedelta(minutes=6)
    #     mock_datetime.datetime.utcnow.return_value = future

    #     self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    #     response = self.client.get(self.protected_url)
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_login_wrong_password(self):
        response = self.client.post(self.login_url, {
            "username": self.user_data["username"],
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("No active account", response.data["detail"])

    def test_invalid_login_nonexistent_user(self):
        response = self.client.post(self.login_url, {
            "username": "notexist",
            "password": "any"
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("No active account", response.data["detail"])

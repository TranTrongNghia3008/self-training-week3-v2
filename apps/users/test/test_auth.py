# apps/users/tests/test_auth.py

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.users.test.factories import UserFactory

User = get_user_model()


class AuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse("register")
        self.login_url = reverse("token_obtain_pair")
        self.logout_url = reverse("logout")
        self.protected_url = "/api/protected/"
        self.user_password = "testpass123"

        self.user = UserFactory(password=self.user_password)

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
            "username": self.user.username,
            "password": self.user_password
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_logout_user_blacklists_token(self):
        login_response = self.client.post(self.login_url, {
            "username": self.user.username,
            "password": self.user_password
        })
        refresh_token = login_response.data["refresh"]

        response = self.client.post(self.logout_url, {"refresh": refresh_token})
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(response.data["message"], "Logout successful")

    def test_invalid_login_wrong_password(self):
        response = self.client.post(self.login_url, {
            "username": self.user.username,
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("No active account", response.data["detail"])

    def test_invalid_login_nonexistent_user(self):
        response = self.client.post(self.login_url, {
            "username": "ghost",
            "password": "any"
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("No active account", response.data["detail"])

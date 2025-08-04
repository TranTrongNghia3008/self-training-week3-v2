from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.blog.models import Category
from apps.users.test.factories import UserFactory
from apps.blog.test.factories import CategoryFactory

class CategoryAPITests(APITestCase):
    def setUp(self):
        self.user = UserFactory(is_staff=False)
        self.admin_user = UserFactory(is_staff=True)

        self.category = CategoryFactory(name="Tech")

        self.list_url = reverse("blog:category-list")
        self.create_url = self.list_url

        # Auth header
        refresh = RefreshToken.for_user(self.admin_user)
        self.admin_auth_header = {
            'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'
        }

        refresh = RefreshToken.for_user(self.user)
        self.user_auth_header = {
            'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'
        }

    def test_list_categories(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["results"][0]["name"], "Tech")

    def test_create_category_as_admin(self):
        payload = {"name": "Science"}
        response = self.client.post(self.create_url, payload, format="json", **self.admin_auth_header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_category_as_non_admin(self):
        payload = {"name": "Unauthorized"}
        response = self.client.post(self.create_url, payload, format="json", **self.user_auth_header)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from apps.blog.models import Category

class CategoryAPITests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Tech")

    def test_list_categories(self):
        url = reverse("blog:category-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Tech")

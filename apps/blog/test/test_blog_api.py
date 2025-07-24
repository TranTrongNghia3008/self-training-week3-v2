from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from apps.users.test.factories import UserFactory
from apps.blog.test.factories import PostFactory, CategoryFactory
from rest_framework_simplejwt.tokens import RefreshToken


class PostAPITests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.category = CategoryFactory()
        self.post = PostFactory(author=self.user, category=self.category)
        self.list_url = reverse('blog:post-list-create')
        self.detail_url = reverse('blog:post-detail', args=[self.post.id])

        # JWT token setup
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.auth_header = {'HTTP_AUTHORIZATION': f'Bearer {self.access_token}'}

    def test_post_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_post_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['author']['id'], self.user.id)

    def test_post_create_unauthenticated(self):
        data = {
            "title": "New Post",
            "content": "Post content",
            "category": self.category.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_authenticated(self):
        data = {
            "title": "New Post",
            "content": "Post content",
            "category": self.category.id,
        }
        response = self.client.post(self.list_url, data, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"]["id"], self.user.id)

    def test_post_update(self):
        data = {
            "title": "Updated Title",
            "content": self.post.content,
            "category": self.category.id,
        }
        response = self.client.put(self.detail_url, data, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Title")

    def test_post_delete(self):
        response = self.client.delete(self.detail_url, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_post_update_unauthorized(self):
        # Another user
        other_user = UserFactory()
        refresh = RefreshToken.for_user(other_user)
        access_token = str(refresh.access_token)
        other_auth = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}

        data = {
            "title": "Hacked",
            "content": self.post.content,
            "category": self.category.id,
        }
        response = self.client.put(self.detail_url, data, **other_auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
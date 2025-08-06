import json
import hashlib
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.test.factories import UserFactory
from apps.blog.test.factories import PostFactory, CategoryFactory


class PostCacheTestCase(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.category = CategoryFactory()
        self.post1 = PostFactory(author=self.user, categories=[self.category])
        self.post2 = PostFactory(author=self.user, categories=[self.category])

        self.list_url = reverse("blog:post-list-create")
        self.detail_url = reverse("blog:post-detail", args=[self.post1.id])

        # JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.auth_header = {'HTTP_AUTHORIZATION': f'Bearer {self.access_token}'}

        # Cache key format
        raw_key = f"posts:list:::page:1"
        self.cache_key = f"posts:{hashlib.md5(raw_key.encode()).hexdigest()}"

        cache.clear()

    def test_post_list_cache_create_and_retrieve(self):
        """Cache is created and reused"""
        self.assertIsNone(cache.get(self.cache_key))

        response = self.client.get(self.list_url, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

        cached_response = cache.get(self.cache_key)
        self.assertIsNotNone(cached_response)
        self.assertEqual(cached_response["count"], 2)

        response2 = self.client.get(self.list_url, **self.auth_header)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data, response.data)

    def test_cache_invalidated_after_post_create(self):
        """POST creation must clear cache"""
        self.client.get(self.list_url, **self.auth_header)
        self.assertIsNotNone(cache.get(self.cache_key))

        data = {
            "title": "New Post",
            "content": "Post content",
            "category_ids": [self.category.id],
        }
        response = self.client.post(self.list_url, data, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIsNone(cache.get(self.cache_key))

        response = self.client.get(self.list_url, **self.auth_header)
        self.assertEqual(response.data["count"], 3)

    def test_cache_is_deleted_after_post_update(self):
        """PUT update must clear cache"""
        self.client.get(self.list_url, **self.auth_header)
        self.assertIsNotNone(cache.get(self.cache_key))

        data = {
            "title": "Updated Title",
            "content": self.post1.content,
            "category_ids": [self.category.id],
        }
        response = self.client.put(self.detail_url, data, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNone(cache.get(self.cache_key), "Cache should be cleared after PUT")

    def test_cache_is_deleted_after_post_delete(self):
        """DELETE must clear cache"""
        self.client.get(self.list_url, **self.auth_header)
        self.assertIsNotNone(cache.get(self.cache_key))

        response = self.client.delete(self.detail_url, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertIsNone(cache.get(self.cache_key), "Cache should be cleared after DELETE")

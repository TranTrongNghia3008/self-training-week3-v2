from rest_framework.test import APITestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from apps.users.test.factories import UserFactory
from apps.blog.test.factories import PostFactory, CategoryFactory
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache


class RelatedPostsAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = UserFactory()
        self.category = CategoryFactory()
        self.now = timezone.now()

        # Bài gốc
        self.post_main = PostFactory(
            author=self.user,
            categories=[self.category],
            title="Django Tutorial",
            content="Learn Django with examples",
            is_published=True,
            scheduled_publish_time=self.now
        )

        # JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.auth_header = {'HTTP_AUTHORIZATION': f'Bearer {self.access_token}'}

        self.related_url = reverse("blog:post-related", args=[self.post_main.id])

    def test_related_posts_found(self):
        related_post = PostFactory(
            author=self.user,
            categories=[self.category],
            title="Advanced Django Guide",
            content="This guide covers advanced Django concepts",
            is_published=True,
            scheduled_publish_time=self.now
        )

        PostFactory(
            author=self.user,
            categories=[self.category],
            title="Cooking Recipes",
            content="Best pasta recipes",
            is_published=True,
            scheduled_publish_time=self.now
        )

        response = self.client.get(self.related_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            any(p["id"] == related_post.id for p in response.data),
        )
        self.assertFalse(
            any(p["id"] == self.post_main.id for p in response.data),
        )

    def test_related_posts_empty(self):
        PostFactory(
            author=self.user,
            categories=[self.category],
            title="Unique Post Title",
            content="Some unique content that won't match anything else",
            is_published=True,
            scheduled_publish_time=self.now
        )

        response = self.client.get(self.related_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_related_posts_unauthenticated(self):
        response = self.client.get(self.related_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

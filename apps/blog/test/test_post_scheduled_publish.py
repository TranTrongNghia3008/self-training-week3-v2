from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.core.cache import cache
from datetime import timedelta

from apps.users.test.factories import UserFactory
from apps.blog.test.factories import PostFactory, CategoryFactory
from rest_framework_simplejwt.tokens import RefreshToken


class ScheduledPublishingTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = UserFactory()
        self.other_user = UserFactory()
        self.category = CategoryFactory()
        self.now = timezone.now()

        # The article is ready to publish.
        self.published_post = PostFactory(
            author=self.user,
            categories=[self.category],
            is_published=True,
            scheduled_publish_time=self.now - timedelta(hours=1)
        )

        # The article is not yet published.
        self.scheduled_post = PostFactory(
            author=self.user,
            categories=[self.category],
            is_published=False,
            scheduled_publish_time=self.now + timedelta(hours=1)
        )

        self.list_url = reverse('blog:post-list-create')
        self.detail_url = lambda pk: reverse('blog:post-detail', args=[pk])

        self.user_token = str(RefreshToken.for_user(self.user).access_token)
        self.other_token = str(RefreshToken.for_user(self.other_user).access_token)

        self.user_auth = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        self.other_auth = {'HTTP_AUTHORIZATION': f'Bearer {self.other_token}'}

    def test_scheduled_post_not_in_list(self):
        """Scheduled posts do not appear in the list before scheduled_publish_time"""
        response = self.client.get(self.list_url, **self.other_auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        post_ids = [post['id'] for post in response.data['results']]
        self.assertIn(self.published_post.id, post_ids)
        self.assertNotIn(self.scheduled_post.id, post_ids)

    def test_scheduled_post_not_accessible_detail(self):
        """Direct access to articles not yet scheduled_publish_time"""
        response = self.client.get(self.detail_url(self.scheduled_post.id), **self.other_auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_scheduled_post_visible_after_time(self):
        """After scheduled_publish_time arrives, the post will appear in the list and be viewable"""
        # Update scheduled_publish_time to simulate "it's time"
        self.scheduled_post.scheduled_publish_time = self.now - timedelta(minutes=1)
        self.scheduled_post.is_published = True
        self.scheduled_post.save()

        response_list = self.client.get(self.list_url)
        post_ids = [post['id'] for post in response_list.data['results']]
        self.assertIn(self.scheduled_post.id, post_ids)

        response_detail = self.client.get(self.detail_url(self.scheduled_post.id))
        self.assertEqual(response_detail.status_code, status.HTTP_200_OK)

    def test_unpublished_post_hidden(self):
        """Unpublished posts (`is_published=False`) should be completely hidden"""
        unpublished_post = PostFactory(
            author=self.user,
            categories=[self.category],
            is_published=False,
            scheduled_publish_time=self.now - timedelta(hours=1)
        )
        response = self.client.get(self.list_url, **self.other_auth)
        post_ids = [post['id'] for post in response.data['results']]
        self.assertNotIn(unpublished_post.id, post_ids)

        response = self.client.get(self.detail_url(unpublished_post.id), **self.other_auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

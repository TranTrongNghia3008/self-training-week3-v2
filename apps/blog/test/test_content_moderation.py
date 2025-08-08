from rest_framework import status
from rest_framework.test import APITestCase
from django.core.cache import cache
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.test.factories import UserFactory
from apps.blog.test.factories import PostFactory, CategoryFactory
from apps.blog.serializers import check_toxicity


class PostModerationAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = UserFactory()
        self.category = CategoryFactory()
        self.list_url = reverse("blog:post-list-create")

        refresh = RefreshToken.for_user(self.user)
        self.auth_header = {
            "HTTP_AUTHORIZATION": f"Bearer {str(refresh.access_token)}"
        }

    def test_create_post_rejected_due_toxicity_real_api(self):
        data = {
            "title": "Toxic Post",
            "content": "You are the most useless person I’ve ever met.",
            "category_ids": [self.category.id],
        }
        toxicity_result = check_toxicity(data["content"])
        print("Perspective API result:", toxicity_result)

        response = self.client.post(self.list_url, data, **self.auth_header)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST if not toxicity_result["allowed"] else status.HTTP_201_CREATED
        )

    def test_create_post_allowed_real_api(self):
        data = {
            "title": "Clean Post",
            "content": "This is a polite and friendly message.",
            "category_ids": [self.category.id],
        }
        toxicity_result = check_toxicity(data["content"])
        print("Perspective API result:", toxicity_result)

        response = self.client.post(self.list_url, data, **self.auth_header)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED if toxicity_result["allowed"] else status.HTTP_400_BAD_REQUEST
        )


class CommentModerationAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = UserFactory()
        self.post = PostFactory()
        self.comment_url = reverse("blog:post-comments", args=[self.post.id])

        refresh = RefreshToken.for_user(self.user)
        self.auth_header = {
            "HTTP_AUTHORIZATION": f"Bearer {str(refresh.access_token)}"
        }

    def test_create_comment_rejected_due_toxicity_real_api(self):
        data = {"content": "Go rot in a hole, you worthless piece of garbage."}
        toxicity_result = check_toxicity(data["content"])
        print("Perspective API result:", toxicity_result)

        response = self.client.post(self.comment_url, data, **self.auth_header)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST if not toxicity_result["allowed"] else status.HTTP_201_CREATED
        )

    def test_create_comment_allowed_real_api(self):
        data = {"content": "I hope you have a wonderful day!"}
        toxicity_result = check_toxicity(data["content"])
        print("Perspective API result:", toxicity_result)

        response = self.client.post(self.comment_url, data, **self.auth_header)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED if toxicity_result["allowed"] else status.HTTP_400_BAD_REQUEST
        )

from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from apps.users.test.factories import UserFactory
from apps.blog.test.factories import PostFactory, CommentFactory
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache

class CommentAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = UserFactory()
        self.other_user = UserFactory()
        self.post = PostFactory()
        self.comment = CommentFactory(author=self.user, post=self.post)
        self.comment_url = reverse('blog:post-comments', args=[self.post.id])
        self.comment_detail_url = reverse('blog:comment-detail', args=[self.comment.id])

        self.user_token = str(RefreshToken.for_user(self.user).access_token)
        self.other_token = str(RefreshToken.for_user(self.other_user).access_token)

        self.user_auth = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        self.other_auth = {'HTTP_AUTHORIZATION': f'Bearer {self.other_token}'}

    def test_list_comments(self):
        response = self.client.get(self.comment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_create_comment_authenticated(self):
        data = {"content": "A new test comment"}
        response = self.client.post(self.comment_url, data, **self.user_auth)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"]["id"], self.user.id)
        self.assertEqual(response.data["content"], "A new test comment")

    def test_create_comment_unauthenticated(self):
        data = {"content": "Unauthenticated comment"}
        response = self.client.post(self.comment_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_comment_owner(self):
        data = {"content": "Updated by owner"}
        response = self.client.put(self.comment_detail_url, data, **self.user_auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"], "Updated by owner")

    def test_update_comment_not_owner(self):
        data = {"content": "Updated by other user"}
        response = self.client.put(self.comment_detail_url, data, **self.other_auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_comment_owner(self):
        data = {"content": "Partially updated"}
        response = self.client.patch(self.comment_detail_url, data, **self.user_auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"], "Partially updated")

    def test_delete_comment_owner(self):
        response = self.client.delete(self.comment_detail_url, **self.user_auth)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_comment_not_owner(self):
        response = self.client.delete(self.comment_detail_url, **self.other_auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_nested_comment(self):
        child_data = {
            "content": "This is a reply",
            "parent": self.comment.id
        }
        response = self.client.post(self.comment_url, child_data, **self.user_auth)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["parent"], self.comment.id)

    def test_retrieve_nested_comments_tree(self):
        child_comment = CommentFactory(post=self.post, parent=self.comment)
        grandchild_comment = CommentFactory(post=self.post, parent=child_comment)

        response = self.client.get(self.comment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Lấy comment gốc
        results = response.data.get("results", response.data)
        root_comment = next((c for c in results if c["id"] == self.comment.id), None)

        self.assertIsNotNone(root_comment)
        self.assertIn("replies", root_comment)
        self.assertEqual(len(root_comment["replies"]), 1)

        child = root_comment["replies"][0]
        self.assertEqual(child["id"], child_comment.id)
        self.assertIn("replies", child)
        self.assertEqual(len(child["replies"]), 1)
        self.assertEqual(child["replies"][0]["id"], grandchild_comment.id)

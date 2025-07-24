from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from apps.users.test.factories import UserFactory
from apps.blog.test.factories import PostFactory, CommentFactory
from rest_framework_simplejwt.tokens import RefreshToken

class CommentAPITests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.post = PostFactory()
        self.comment_url = reverse('blog:post-comments', args=[self.post.id])
        self.comment = CommentFactory(author=self.user, post=self.post)

        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.auth = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

    def test_list_comments(self):
        response = self.client.get(self.comment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_comment_authenticated(self):
        data = {"content": "A test comment"}
        response = self.client.post(self.comment_url, data, **self.auth)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"]["id"], self.user.id)

    def test_create_comment_unauthenticated(self):
        data = {"content": "A test comment"}
        response = self.client.post(self.comment_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
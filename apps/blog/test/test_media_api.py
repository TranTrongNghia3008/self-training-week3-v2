from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from apps.users.test.factories import UserFactory
from apps.blog.test.factories import PostFactory, MediaFactory
from django.core.files.uploadedfile import SimpleUploadedFile

class MediaAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = UserFactory()
        self.other_user = UserFactory()

        self.post = PostFactory(author=self.user)
        self.other_post = PostFactory(author=self.other_user)

        self.media = MediaFactory(post=self.post)
        self.media_detail_url = reverse('blog:media-detail', args=[self.media.id])
        self.media_list_url = reverse('blog:media-list-create')

        self.user_token = str(RefreshToken.for_user(self.user).access_token)
        self.other_token = str(RefreshToken.for_user(self.other_user).access_token)

        self.user_auth = {'HTTP_AUTHORIZATION': f'Bearer {self.user_token}'}
        self.other_auth = {'HTTP_AUTHORIZATION': f'Bearer {self.other_token}'}

    def test_list_media(self):
        response = self.client.get(self.media_list_url, **self.user_auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_create_media_authenticated_owner(self):
        image_file = SimpleUploadedFile(
            "test.jpg",
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04\x00\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4C\x01\x00\x3B",
            content_type="image/gif"
        )
        data = {
            "post": self.post.id,
            "file": image_file,
            "type": "image"
        }
        response = self.client.post(self.media_list_url, data, **self.user_auth)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["post"], str(self.post.id))

    def test_create_media_authenticated_not_owner(self):
        image_file = SimpleUploadedFile(
            "test.jpg",
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04\x00\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4C\x01\x00\x3B",
            content_type="image/gif"
        )
        data = {
            "post": self.other_post.id,
            "file": image_file,
            "type": "image"
        }
        response = self.client.post(self.media_list_url, data, **self.user_auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_media_unauthenticated(self):
        image_file = SimpleUploadedFile(
            "test.jpg",
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04\x00\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4C\x01\x00\x3B",
            content_type="image/gif"
        )
        data = {
            "post": self.post.id,
            "file": image_file,
            "type": "image"
        }
        response = self.client.post(self.media_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_media_owner(self):
        new_data = {
            "type": "image",
            "file": self.media.file,  # fake URL used
            "post": self.post.id
        }
        response = self.client.put(self.media_detail_url, new_data, **self.user_auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["type"], "image")

    def test_update_media_not_owner(self):
        new_data = {
            "type": "image",
            "file": self.media.file,
            "post": self.post.id
        }
        response = self.client.put(self.media_detail_url, new_data, **self.other_auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_media_owner(self):
        response = self.client.patch(self.media_detail_url, {"type": "image"}, **self.user_auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["type"], "image")

    def test_delete_media_owner(self):
        response = self.client.delete(self.media_detail_url, **self.user_auth)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_media_not_owner(self):
        response = self.client.delete(self.media_detail_url, **self.other_auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

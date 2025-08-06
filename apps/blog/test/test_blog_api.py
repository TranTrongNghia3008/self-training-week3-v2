from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from apps.users.test.factories import UserFactory
from apps.blog.test.factories import PostFactory, CategoryFactory
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache


class PostAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = UserFactory()
        self.category = CategoryFactory()
        self.post = PostFactory(author=self.user, categories=[self.category])

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
            "categories": [self.category.id],
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_authenticated(self):
        data = {
            "title": "New Post",
            "content": "Post content",
            "category_ids": [self.category.id],
        }
        response = self.client.post(self.list_url, data, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"]["id"], self.user.id)
        category_ids = {cat["id"] for cat in response.data["categories"]}
        self.assertEqual(category_ids, {self.category.id})

    def test_post_update(self):
        new_category = CategoryFactory()
        data = {
            "title": "Updated Title",
            "content": self.post.content,
            "category_ids": [new_category.id],
        }
        response = self.client.put(self.detail_url, data, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Title")
        category_ids = {cat["id"] for cat in response.data["categories"]}
        self.assertEqual(category_ids, {new_category.id})

    def test_post_delete(self):
        response = self.client.delete(self.detail_url, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_post_update_unauthorized(self):
        other_user = UserFactory()
        refresh = RefreshToken.for_user(other_user)
        access_token = str(refresh.access_token)
        other_auth = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}

        new_category = CategoryFactory()
        data = {
            "title": "Hacked",
            "content": self.post.content,
            "categories": [new_category.id],
        }
        response = self.client.put(self.detail_url, data, **other_auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_filter_by_search(self):
        PostFactory(title="FastAPI vs Django", author=self.user)
        PostFactory(title="Random title", author=self.user)

        response = self.client.get(f"{self.list_url}?search=FastAPI")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all("FastAPI" in post["title"] for post in response.data["results"]))

    def test_post_filter_by_category(self):
        new_category = CategoryFactory()
        post1 = PostFactory(author=self.user, categories=[new_category])
        post2 = PostFactory(author=self.user, categories=[new_category])

        response = self.client.get(f"{self.list_url}?category={new_category.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for post in response.data["results"]:
            category_ids = [cat["id"] for cat in post["categories"]]
            self.assertIn(new_category.id, category_ids)

    def test_post_pagination(self):
        PostFactory.create_batch(15, author=self.user)
        for post in PostFactory.create_batch(5, author=self.user, categories=[self.category]):
            pass  # categories already added via factory

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)  # default page size

        response_page_2 = self.client.get(f"{self.list_url}?page=2")
        self.assertEqual(response_page_2.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response_page_2.data["results"]) > 0)

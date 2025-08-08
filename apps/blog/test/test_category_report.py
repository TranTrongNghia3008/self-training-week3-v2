from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from apps.users.test.factories import UserFactory
from apps.blog.test.factories import PostFactory, CategoryFactory, CommentFactory
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache

class CategoryReportAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin_user = UserFactory(is_staff=True)
        self.user = UserFactory(is_staff=False)

        # Tạo categories
        self.cat_tech = CategoryFactory(name="Tech")
        self.cat_food = CategoryFactory(name="Food")

        # Tạo bài viết thuộc Tech với views và comments
        self.post1 = PostFactory(
            author=self.user,
            categories=[self.cat_tech],
            title="Tech post 1",
            is_published=True,
            views=10,
            scheduled_publish_time=timezone.now()
        )
        CommentFactory.create_batch(3, post=self.post1)

        # Tạo bài viết thuộc Food với views và comments
        self.post2 = PostFactory(
            author=self.user,
            categories=[self.cat_food],
            title="Food post 1",
            is_published=True,
            views=5,
            scheduled_publish_time=timezone.now()
        )
        CommentFactory.create_batch(1, post=self.post2)

        # Tạo bài viết mới (trong 7 ngày) cho Tech category
        self.recent_post = PostFactory(
            author=self.user,
            categories=[self.cat_tech],
            title="Recent Tech Post",
            is_published=True,
            views=7,
            scheduled_publish_time=timezone.now()
        )

        # URL của API báo cáo (giả sử bạn đã khai báo trong urls.py)
        self.url = reverse('blog:category-report')

        # Admin token header
        refresh = RefreshToken.for_user(self.admin_user)
        self.admin_auth_header = {
            'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'
        }

    def test_category_report_access_by_admin(self):
        response = self.client.get(self.url, **self.admin_auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Kiểm tra dữ liệu trả về cho từng category
        data = response.data
        tech_data = next((c for c in data if c["id"] == self.cat_tech.id), None)
        food_data = next((c for c in data if c["id"] == self.cat_food.id), None)

        self.assertIsNotNone(tech_data)
        self.assertIsNotNone(food_data)

        # Kiểm tra tổng views và comments
        self.assertEqual(tech_data["total_views"], self.post1.views + self.recent_post.views)
        self.assertEqual(food_data["total_views"], self.post2.views)

        self.assertEqual(tech_data["total_comments"], 3)  # post1 có 3 comment
        self.assertEqual(food_data["total_comments"], 1)  # post2 có 1 comment

        # Kiểm tra số bài mới trong 30 ngày (mặc định)
        self.assertTrue(tech_data.get("new_posts", 0) >= 1)
        self.assertTrue(food_data.get("new_posts", 0) >= 1)

    def test_category_report_access_denied_for_non_admin(self):
        refresh = RefreshToken.for_user(self.user)
        user_auth_header = {'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'}

        response = self.client.get(self.url, **user_auth_header)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_category_report_access_denied_for_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

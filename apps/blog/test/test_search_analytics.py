from rest_framework.test import APITestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from apps.users.test.factories import UserFactory
from apps.blog.test.factories import PostFactory, CategoryFactory
from apps.blog.models import SearchQueryLog
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache

class SearchAnalyticsAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin_user = UserFactory(is_staff=True, is_superuser=True)
        self.normal_user = UserFactory()
        self.category = CategoryFactory()
        self.now = timezone.now()

        # Tạo vài bài post phục vụ search
        self.post1 = PostFactory(title="Django testing tips", author=self.normal_user, categories=[self.category], is_published=True, scheduled_publish_time=self.now)
        self.post2 = PostFactory(title="FastAPI and Django", author=self.normal_user, categories=[self.category], is_published=True, scheduled_publish_time=self.now)

        # URLs
        self.search_list_url = reverse('blog:post-list-create')
        self.search_analytics_url = reverse('blog:search-analytics') 
        self.search_click_url = reverse('blog:search-click-update')

        # Tokens
        refresh = RefreshToken.for_user(self.admin_user)
        self.admin_auth_header = {'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'}

        refresh_user = RefreshToken.for_user(self.normal_user)
        self.user_auth_header = {'HTTP_AUTHORIZATION': f'Bearer {str(refresh_user.access_token)}'}

    def test_search_logs_created_on_search(self):
        # Call search API
        response = self.client.get(f"{self.search_list_url}?search=Django")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the generated log
        logs = SearchQueryLog.objects.filter(keyword="Django")
        self.assertTrue(logs.exists())
        self.assertEqual(logs.first().results_count, 2)  # Both posts have "Django" in the title

    def test_search_analytics_access_by_admin(self):
        # Create some simulation logs
        SearchQueryLog.objects.create(keyword="Django", results_count=3, clicked=True)
        SearchQueryLog.objects.create(keyword="Django", results_count=5, clicked=False)
        SearchQueryLog.objects.create(keyword="FastAPI", results_count=2, clicked=True)
        SearchQueryLog.objects.create(keyword="NoResults", results_count=0, clicked=False)

        response = self.client.get(self.search_analytics_url, **self.admin_auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn("popular_keywords", data)
        self.assertIn("low_results_keywords", data)

        # Check the returned data for the generated keywords
        popular_keywords = {item['keyword'] for item in data['popular_keywords']}
        self.assertIn("Django", popular_keywords)
        self.assertIn("FastAPI", popular_keywords)

        low_results_keywords = {item['keyword'] for item in data['low_results_keywords']}
        self.assertIn("NoResults", low_results_keywords)

    def test_search_analytics_forbidden_for_non_admin(self):
        response = self.client.get(self.search_analytics_url, **self.user_auth_header)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_click_update(self):
        # Create log clicked=False
        log = SearchQueryLog.objects.create(keyword="Django", results_count=3, clicked=False)
        
        response = self.client.post(self.search_click_url, {"keyword": "Django"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh from db and check clicked is changed to True
        log.refresh_from_db()
        self.assertTrue(log.clicked)

    def test_search_click_update_no_log(self):
        response = self.client.post(self.search_click_url, {"keyword": "UnknownKeyword"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_search_click_update_no_keyword(self):
        response = self.client.post(self.search_click_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

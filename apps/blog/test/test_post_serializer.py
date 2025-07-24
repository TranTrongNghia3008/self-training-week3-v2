from rest_framework.test import APITestCase
from apps.users.models import User
from apps.blog.models import Post, Comment, Category
from apps.blog.serializers import PostSerializer
from apps.users.serializers import UserSerializer
from apps.blog.test.factories import UserFactory, PostFactory, CommentFactory, CategoryFactory


class PostSerializerTests(APITestCase):
    def setUp(self):
        self.user = UserFactory(username="nesteduser")
        self.category = CategoryFactory(name="Tech")
        self.post = PostFactory(author=self.user, category=self.category)
        self.comment1 = CommentFactory(author=self.user, post=self.post, content="First!")
        self.comment2 = CommentFactory(author=self.user, post=self.post, content="Second!")

    def test_post_serializer_nested_fields(self):
        serializer = PostSerializer(instance=self.post)
        data = serializer.data

        # Top-level fields
        self.assertEqual(data["id"], self.post.id)
        self.assertEqual(data["title"], self.post.title)
        self.assertEqual(data["author"]["id"], self.user.id)
        self.assertEqual(data["author"]["username"], self.user.username)

        # Nested comments
        self.assertIn("comments", data)
        self.assertEqual(len(data["comments"]), 2)

        # Check comment content and nested author
        first_comment = data["comments"][0]
        self.assertEqual(first_comment["author"]["id"], self.user.id)
        self.assertEqual(first_comment["content"], "First!")

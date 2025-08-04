from rest_framework.test import APITestCase
from apps.blog.models import Post, Comment, Category
from apps.blog.serializers import PostSerializer
from apps.blog.test.factories import UserFactory, PostFactory, CommentFactory, CategoryFactory


class PostSerializerTests(APITestCase):
    def setUp(self):
        self.user = UserFactory(username="nesteduser")
        self.category = CategoryFactory(name="Tech")
        self.post = PostFactory(author=self.user)
        self.post.categories.add(self.category)  # many-to-many

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

        # Categories
        self.assertIn("categories", data)
        self.assertEqual(len(data["categories"]), 1)
        self.assertEqual(data["categories"][0]["id"], self.category.id)
        self.assertEqual(data["categories"][0]["name"], self.category.name)

        # Nested comments
        self.assertIn("comments", data)
        self.assertEqual(len(data["comments"]), 2)

        # Check comment content and nested author
        comment_contents = [comment["content"] for comment in data["comments"]]
        self.assertIn("First!", comment_contents)
        self.assertIn("Second!", comment_contents)

        for comment in data["comments"]:
            self.assertEqual(comment["author"]["id"], self.user.id)
            self.assertEqual(comment["author"]["username"], self.user.username)

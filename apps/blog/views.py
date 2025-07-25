from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from .models import Post, Comment, Category
from .serializers import PostSerializer, CommentSerializer, CategorySerializer
from apps.core.permissions import IsOwnerOrReadOnly
from apps.notifications.tasks import send_notification_email

class PostPagination(PageNumberPagination):
    page_size = 10

class PostListCreateAPIView(generics.ListCreateAPIView):
    queryset = Post.objects.all().select_related("author", "category").prefetch_related("comments")
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = PostPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class PostRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsOwnerOrReadOnly]

class CommentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(post_id=self.kwargs["post_id"])

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user, post_id=self.kwargs["post_id"])

        post_author_email = comment.post.author.email
        subject = f"New Comment on Your Post '{comment.post.title}'"
        message = f"{self.request.user.username} commented: {comment.content}"

        send_notification_email.delay(subject, message, post_author_email)

class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

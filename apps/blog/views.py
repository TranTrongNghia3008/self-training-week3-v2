from rest_framework import generics, permissions, parsers
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound
from .models import Post, Comment, Category, Media
from .serializers import PostSerializer, CommentSerializer, CategorySerializer, MediaSerializer
from apps.core.permissions import IsOwnerOrReadOnly, ReadOnlyOrAdminCreatePermission
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class PostPagination(PageNumberPagination):
    page_size = 10

class PostListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = PostPagination

    def get_queryset(self):
        queryset = Post.objects.all().select_related("author").prefetch_related("comments", "categories").order_by("-created_at")

        search = self.request.query_params.get("search")
        category_ids = self.request.query_params.get("category")  # expects comma-separated values

        if search:
            queryset = queryset.filter(title__icontains=search)

        if category_ids:
            try:
                ids = [int(cid) for cid in category_ids.split(",") if cid.strip().isdigit()]
                if ids:
                    queryset = queryset.filter(categories__in=ids).distinct()
            except ValueError:
                pass 
        return queryset


    @swagger_auto_schema(
        tags=["Post"],
        manual_parameters=[
            openapi.Parameter(
                name="search",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Search by title keyword",
            ),
            openapi.Parameter(
                name="category",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,  # đổi từ INTEGER → STRING để hỗ trợ nhiều giá trị
                description="Comma-separated category IDs (e.g., ?category=1,2,3)",
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Post"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, views=0)

class PostRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsOwnerOrReadOnly]

    @swagger_auto_schema(tags=["Post"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Post"])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Post"])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Post"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
class CommentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(post_id=self.kwargs["post_id"])

    @swagger_auto_schema(tags=["Comment"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Comment"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        try:
            post = Post.objects.get(id=self.kwargs["post_id"])
        except Post.DoesNotExist:
            raise NotFound("Post not found")
        serializer.save(author=self.request.user, post=post)

class CategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [ReadOnlyOrAdminCreatePermission]

    @swagger_auto_schema(tags=["Category"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Category"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()

class MediaListCreateAPIView(generics.ListCreateAPIView):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    @swagger_auto_schema(
        tags=["Media"],
        operation_description="Upload a single media file (image/video)",
        manual_parameters=[
            openapi.Parameter(
                name="file",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description="Media file to upload (image or video)",
                required=True,
            ),
            openapi.Parameter(
                name="post",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                description="Post ID this media belongs to",
                required=True,
            ),
        ],
        responses={201: MediaSerializer(), 400: "Validation error", 404: "Post not found"},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Media"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class MediaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    permission_classes = [IsOwnerOrReadOnly]

    @swagger_auto_schema(tags=["Media"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Media"])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Media"])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Media"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

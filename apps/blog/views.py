from django.core.cache import cache
import hashlib

from rest_framework import generics, permissions, parsers
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Post, Comment, Category, Media
from .serializers import PostSerializer, CommentSerializer, CategorySerializer, MediaSerializer
from apps.core.permissions import IsOwnerOrReadOnly, ReadOnlyOrAdminCreatePermission
from apps.core.utils import delete_cache_by_prefix

class PostPagination(PageNumberPagination):
    page_size = 10

class PostListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = PostPagination

    def get_queryset(self):
        return Post.objects.all().select_related("author").prefetch_related("comments", "categories").order_by("-created_at")

    def list(self, request, *args, **kwargs):
        search = request.query_params.get("search", "")
        category_ids = request.query_params.get("category", "")
        page = request.query_params.get("page", "1")

        # Generate consistent cache key
        raw_key = f"posts:list:{search}:{category_ids}:page:{page}"
        cache_key = f"posts:{hashlib.md5(raw_key.encode()).hexdigest()}"

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        # Get queryset and apply filters
        queryset = self.filter_queryset(self.get_queryset())

        if search:
            queryset = queryset.filter(title__icontains=search)

        if category_ids:
            try:
                ids = [int(cid) for cid in category_ids.split(",") if cid.strip().isdigit()]
                if ids:
                    queryset = queryset.filter(categories__in=ids).distinct()
            except ValueError:
                pass

        page_obj = self.paginate_queryset(queryset)
        if page_obj is not None:
            serializer = self.get_serializer(page_obj, many=True)
            response_data = self.get_paginated_response(serializer.data).data
            cache.set(cache_key, response_data, timeout=60)
            return Response(response_data)

        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        cache.set(cache_key, data, timeout=60)
        return Response(data)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, views=0)
        delete_cache_by_prefix("posts:")

    @swagger_auto_schema(
        tags=["Post"],
        manual_parameters=[
            openapi.Parameter(
                name="search",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Search by title",
            ),
            openapi.Parameter(
                name="category",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Comma-separated category IDs",
            ),
            openapi.Parameter(
                name="page",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="Page number",
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Post"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
class PostRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def perform_update(self, serializer):
        serializer.save()
        delete_cache_by_prefix("posts:")

    def perform_destroy(self, instance):
        instance.delete()
        delete_cache_by_prefix("posts:")

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

from django.core.cache import cache
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
import hashlib

from rest_framework import generics, permissions, parsers
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView


from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Post, Comment, Category, Media, SearchQueryLog
from .serializers import PostSerializer, CommentSerializer, CategorySerializer, MediaSerializer, CategoryReportSerializer
from apps.core.permissions import IsOwnerOrReadOnly, ReadOnlyOrAdminCreatePermission, CanViewPost, IsMediaOwnerOrAdmin, CanAddMediaToOwnPost
from apps.core.utils import delete_cache_by_prefix

class PostPagination(PageNumberPagination):
    page_size = 10

class PostListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [CanViewPost, permissions.IsAuthenticatedOrReadOnly]
    pagination_class = PostPagination

    def get_queryset(self):
        queryset = Post.objects.select_related("author").prefetch_related("comments", "categories")

        user = self.request.user
        if user.is_staff or user.is_superuser:
            return queryset.order_by("-created_at")

        if user.is_authenticated:
            return queryset.filter(
                Q(is_published=True, scheduled_publish_time__lte=timezone.now()) |
                Q(author=user)
            ).order_by("-created_at")

        return queryset.filter(
            is_published=True,
            scheduled_publish_time__lte=timezone.now()
        ).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        search = request.query_params.get("search", "").strip()
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

        # Count the number of returned results (before pagination)
        total_results = queryset.count()

        # Search Logging
        if search:
            SearchQueryLog.objects.create(
                keyword=search,
                results_count=total_results,
                clicked=False  
            )

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
    permission_classes = [CanViewPost, IsOwnerOrReadOnly]

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
    
class RelatedPostsAPIView(generics.GenericAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # Không phân trang

    def get_queryset(self):
        queryset = Post.objects.select_related("author").prefetch_related("comments", "categories")
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return queryset
        if user.is_authenticated:
            return queryset.filter(
                Q(is_published=True, scheduled_publish_time__lte=timezone.now()) |
                Q(author=user)
            )
        return queryset.filter(
            is_published=True,
            scheduled_publish_time__lte=timezone.now()
        )

    @swagger_auto_schema(
        tags=["Post"],
        manual_parameters=[
            openapi.Parameter(
                name="post_id",
                in_=openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
                description="ID của bài viết gốc"
            ),
        ]
    )
    def get(self, request, post_id):
        # Cache
        cache_key = f"related_posts:{post_id}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        # Lấy bài gốc
        post = get_object_or_404(self.get_queryset(), id=post_id)

        # SearchVector + SearchQuery
        vector = SearchVector('title', weight='A') + SearchVector('content', weight='B')
        query = SearchQuery(post.title) | SearchQuery(post.content)

        # Lấy bài liên quan
        related_posts = (
            self.get_queryset()
            .annotate(rank=SearchRank(vector, query))
            .filter(rank__gte=0.1)
            .exclude(id=post.id)
            .order_by('-rank')[:5]
        )

        serializer = self.get_serializer(related_posts, many=True)
        data = serializer.data
        cache.set(cache_key, data, timeout=60)
        return Response(data)

    
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

class CommentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.select_related("author", "post")
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    @swagger_auto_schema(tags=["Comment"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Comment"])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Comment"])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Comment"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
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
        try:
            post = Post.objects.get(id=self.kwargs["post_id"])
        except Post.DoesNotExist:
            raise NotFound("Post not found")

        parent_id = self.request.data.get("parent")
        parent = None
        if parent_id:
            try:
                parent = Comment.objects.get(id=parent_id, post=post)
            except Comment.DoesNotExist:
                raise NotFound("Parent comment not found")

        serializer.save(author=self.request.user, post=post, parent=parent)

class CategoryReportAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        days_ago = request.query_params.get("days", 30)
        try:
            days_ago = int(days_ago)
        except ValueError:
            days_ago = 30

        since_date = timezone.now() - timezone.timedelta(days=days_ago)

        categories = Category.objects.annotate(
            total_views=Sum('posts__views', distinct=True),
            total_comments=Count('posts__comments', distinct=True),
            new_posts=Count('posts', filter=Q(posts__created_at__gte=since_date)),
        ).order_by('-total_views')

        # Chuẩn bị data dạng dict cho serializer
        data = []
        for cat in categories:
            data.append({
                "id": cat.id,
                "name": cat.name,
                "total_views": cat.total_views or 0,
                "total_comments": cat.total_comments or 0,
                "new_posts": cat.new_posts or 0,
            })

        # Khởi tạo serializer với many=True
        serializer = CategoryReportSerializer(data, many=True)
        return Response(serializer.data)

class MediaListCreateAPIView(generics.ListCreateAPIView):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    permission_classes = [permissions.IsAuthenticated, CanAddMediaToOwnPost]
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
    permission_classes = [IsMediaOwnerOrAdmin]

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

class SearchAnalyticsAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        days_ago = request.query_params.get("days", 30)
        try:
            days_ago = int(days_ago)
        except ValueError:
            days_ago = 30

        since_date = timezone.now() - timezone.timedelta(days=days_ago)

        logs = SearchQueryLog.objects.filter(timestamp__gte=since_date)

        popular_keywords = logs.values('keyword').annotate(
            search_count=Count('id'),
            click_count=Count('id', filter=Q(clicked=True)),
            avg_results=Sum('results_count') / Count('id'),
        ).order_by('-search_count')[:10]

        # Keywords with few or no results (e.g. results_count <= 3)
        low_results_keywords = logs.values('keyword').annotate(
            search_count=Count('id'),
            avg_results=Sum('results_count') / Count('id'),
        ).filter(avg_results__lte=3).order_by('avg_results')[:10]

        return Response({
            "popular_keywords": list(popular_keywords),
            "low_results_keywords": list(low_results_keywords),
        })
    
class SearchClickUpdateAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        keyword = request.data.get("keyword", "").strip()
        if not keyword:
            return Response({"detail": "Keyword required"}, status=400)

        # Update the most recent search log for this keyword (assuming new user click)
        log = SearchQueryLog.objects.filter(keyword=keyword, clicked=False).order_by('-timestamp').first()
        if log:
            log.clicked = True
            log.save()
            return Response({"detail": "Click updated"})
        return Response({"detail": "No log entry found to update"}, status=404)

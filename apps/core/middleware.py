from apps.blog.models import Post
from django.utils.deprecation import MiddlewareMixin
from django.db import models

class PostViewCountMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Only count views for GET requests on post detail views
        if request.method == "GET" and request.path.startswith("/api/blog/posts/"):
            try:
                # Extract post_id from the view kwargs
                post_id = view_kwargs.get("pk")
                if post_id:
                    Post.objects.filter(pk=post_id).update(views=models.F("views") + 1)
            except Exception as e:
                print("Error counting views:", e)
        return None

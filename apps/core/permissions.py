from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import NotFound
from django.utils import timezone
from apps.blog.models import Post

class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission: Allow read-only access to any user,
    but only allow write access to the owner of the object.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user
    
class ReadOnlyOrAdminCreatePermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff  
    
class CanViewPost(BasePermission):
    """
    Allow viewing of posts if:
        - Admin/staff
        - Author
        - Post has been published and has reached scheduled_publish_time
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True

        if obj.author == request.user:
            return True

        if request.method in SAFE_METHODS:
            return obj.is_published and obj.scheduled_publish_time <= timezone.now()

        return False 
class IsMediaOwnerOrAdmin(BasePermission):
    """
    Allows:
        - Admin
        - Author of post containing media
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True

        return obj.post.author == request.user

class CanAddMediaToOwnPost(BasePermission):
    """
    Only allow adding media if the user is the author of the post or a staff member
    """

    def has_permission(self, request, view):
        if request.method != "POST":
            return True 

        post_id = request.data.get("post")
        if not post_id:
            return False 

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise NotFound("Post not found.")

        view.post_instance = post

        return post.author == request.user or request.user.is_staff
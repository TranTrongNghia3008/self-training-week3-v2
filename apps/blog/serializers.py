from rest_framework import serializers
from .models import Category, Post, Comment, Media
from apps.users.serializers import UserSerializer
import cloudinary
from .models import Media
class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "author", "content", "created_at"]

class MediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = ["id", "post", "file_url", "type", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at", "type"]

    def create(self, validated_data):
        request = self.context.get("request")
        uploaded_file = request.FILES.get("file")
        post_id = request.data.get("post")

        if not uploaded_file:
            raise serializers.ValidationError("No file uploaded.")

        content_type = uploaded_file.content_type.lower()
        media_type = "video" if "video" in content_type else "image"

        upload_result = cloudinary.uploader.upload(
            uploaded_file,
            resource_type=media_type,
        )

        media = Media.objects.create(
            post_id=post_id,
            file=upload_result["secure_url"],
            type=media_type,
        )
        return media

    def get_file_url(self, obj):
        return obj.file

class MediaUploadSerializer(serializers.Serializer):
    file = serializers.FileField(write_only=True)
    post = serializers.IntegerField()

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    medias = MediaSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ["id", "author", "category", "title", "content", "is_published", "created_at", "updated_at", "comments", "views", "medias"]
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]

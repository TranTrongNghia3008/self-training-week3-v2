import cloudinary
from rest_framework import serializers
from django.utils.text import slugify
from django.utils import timezone
from .models import Category, Post, Comment, Media
from apps.users.serializers import UserSerializer

class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies = RecursiveField(many=True, read_only=True)
    parent = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Comment
        fields = ["id", "author", "content", "created_at", "parent", "replies"]

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


class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug"]

    def create(self, validated_data):
        if "slug" not in validated_data or not validated_data["slug"]:
            validated_data["slug"] = slugify(validated_data["name"])
        return super().create(validated_data)

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    comments = serializers.SerializerMethodField()
    medias = MediaSerializer(many=True, read_only=True)

    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True,
        write_only=True,
        source="categories"
    )
    scheduled_publish_time = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = Post
        fields = [
            "id", "author", "title", "content", "is_published", "scheduled_publish_time", "created_at", "updated_at", "comments", "views", "medias", "categories", "category_ids"
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at", "comments", "views", "medias", "categories"]

    def get_comments(self, obj):
        root_comments = obj.comments.filter(parent=None).order_by("created_at")
        return CommentSerializer(root_comments, many=True).data


    def create(self, validated_data):
        categories = validated_data.pop("categories", [])
        post = Post.objects.create(**validated_data)
        post.categories.set(categories)
        return post

    def update(self, instance, validated_data):
        categories = validated_data.pop("categories", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if categories is not None:
            instance.categories.set(categories)
        return instance

    def validate(self, attrs):
        scheduled_time = attrs.get("scheduled_publish_time")
        is_published = attrs.get("is_published", False)

        if scheduled_time:
            if scheduled_time < timezone.now():
                raise serializers.ValidationError("Scheduled publish time cannot be in the past.")
            if is_published:
                raise serializers.ValidationError("Post cannot be published before the scheduled publish time.")

        return attrs
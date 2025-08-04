from django.contrib import admin
from .models import Category, Post, Comment, Media

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "get_categories", "is_published", "created_at")  # Sửa tại đây
    list_filter = ("is_published", "categories")
    search_fields = ("title", "content")

    def get_categories(self, obj):
        return ", ".join([cat.name for cat in obj.categories.all()])
    get_categories.short_description = "Categories"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "created_at")
    search_fields = ("content",)

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ("post", "file", "type", "uploaded_at")
    search_fields = ("file",)
    list_filter = ("type",)

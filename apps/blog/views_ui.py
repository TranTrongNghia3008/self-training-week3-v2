from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404
from django.contrib import messages

from .models import Post, Comment, Category
from apps.notifications.tasks import send_notification_email

class PostListView(ListView):
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.select_related("author", "category").prefetch_related("comments").order_by("-created_at")


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ["title", "content", "category"]
    template_name = "blog/post_form.html"
    success_url = reverse_lazy("blog_ui:post-list-html")

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, "Post created successfully.")
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ["title", "content", "category"]
    template_name = "blog/post_form.html"
    success_url = reverse_lazy("blog_ui:post-list-html")

    def test_func(self):
        post = self.get_object()
        return post.author == self.request.user


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = "blog/post_confirm_delete.html"
    success_url = reverse_lazy("blog_ui:post-list-html")

    def test_func(self):
        post = self.get_object()
        return post.author == self.request.user


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ["content"]
    template_name = "blog/comment_form.html"

    def form_valid(self, form):
        post_id = self.kwargs["post_id"]
        post = get_object_or_404(Post, pk=post_id)
        form.instance.post = post
        form.instance.author = self.request.user

        # Send notification
        post_author_email = post.author.email
        subject = f"New Comment on Your Post '{post.title}'"
        message = f"{self.request.user.username} commented: {form.cleaned_data['content']}"
        send_notification_email.delay(subject, message, post_author_email)

        messages.success(self.request, "Comment added successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("blog_ui:post-detail-html", kwargs={"pk": self.kwargs["post_id"]})

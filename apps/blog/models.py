from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.notifications.tasks import send_notification_email

User = settings.AUTH_USER_MODEL

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="posts")
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_published = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
# Connect signal to send email when a post is created
@receiver(post_save, sender=Post)
def send_email_on_post_created(sender, instance, created, **kwargs):
    if created:
        send_notification_email.delay(
            subject=f"New Post Created: {instance.title}",
            message=f"Author: {instance.author.username}\n\n{instance.content}",
            recipient_email="admin@example.com"
        )

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.post}"

# Connect signal to send email when a comment is created
@receiver(post_save, sender=Comment)
def send_email_on_comment_created(sender, instance, created, **kwargs):
    if created:
        post_author_email = instance.post.author.email
        subject = f"New Comment on Your Post '{instance.post.title}'"
        message = f"{instance.author.username} commented: {instance.content}"
        
        send_notification_email.delay(subject, message, post_author_email)
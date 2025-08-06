from celery import shared_task
from django.utils import timezone
from .models import Post

@shared_task
def publish_scheduled_posts():    
    now = timezone.now()
    print(">>> Running publish_scheduled_posts at", now)
    posts = Post.objects.filter(
        is_published=False,
        scheduled_publish_time__lte=now
    )
    updated_count = posts.update(is_published=True)
    return f"{updated_count} posts published."

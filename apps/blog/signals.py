from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete
from django.contrib.contenttypes.models import ContentType
from .models import Comment
from apps.notifications.models import Notification

@receiver(post_save, sender=Comment)
def notify_on_comment_save(sender, instance, created, **kwargs):
    print(f"[Signal] Comment {'created' if created else 'updated'}: {instance.id} - {instance.content}")

    channel_layer = get_channel_layer()
    comment_data = {
        "id": instance.id,
        "author": instance.author.username,
        "content": instance.content,
        "created_at": instance.created_at.isoformat(),
    }

    # Send comment information to people viewing the article
    async_to_sync(channel_layer.group_send)(
        f"post_{instance.post.id}",
        {
            "type": "comment_event",
            "data": {
                "action": "created" if created else "updated",
                "comment": comment_data,
            },
        }
    )

    if not created:
        return 

    notified_user_ids = set()

    # 1. Prioritize sending notifications to parent comment author (if different from commenter)
    if instance.parent and instance.parent.author.id != instance.author.id:
        Notification.objects.create(
            recipient=instance.parent.author,
            message=f"{instance.author.username} replied to your comment on: {instance.post.title}",
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
        )
        notified_user_ids.add(instance.parent.author.id)

    # 2. Send notification to post author if:
    # - the commenter is not the post author
    # - and has not received notification in the above step
    if (
        instance.post.author.id != instance.author.id and
        instance.post.author.id not in notified_user_ids
    ):
        Notification.objects.create(
            recipient=instance.post.author,
            message=f"{instance.author.username} commented on your post: {instance.post.title}",
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
        )

@receiver(pre_delete, sender=Comment)
def notify_on_comment_delete(sender, instance, **kwargs):
    print(f"[SIGNAL] Comment deleted: id={instance.id}, post_id={instance.post.id}")

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"post_{instance.post.id}",
        {
            "type": "comment_event",
            "data": {
                "action": "deleted",
                "comment_id": instance.id,
            },
        }
    )

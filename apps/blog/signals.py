from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete
from django.contrib.contenttypes.models import ContentType
from .models import Comment
from apps.notifications.models import Notification

@receiver(post_save, sender=Comment)
def notify_on_comment_save(sender, instance, created, **kwargs):
    print(f"[Signal] Comment {'created' if created else 'updated'}: {instance.id}")

    channel_layer = get_channel_layer()
    comment_data = {
        "id": instance.id,
        "author": instance.author.username,
        "content": instance.content,
        "created_at": instance.created_at.isoformat(),
    }

    # Gửi thông tin comment cho người đang xem bài viết
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

    # Gửi thông báo nếu không phải tác giả comment tự comment vào bài của mình
    if created and instance.post.author.id != instance.author.id:
        recipient = instance.post.author

        # Save to DB
        notification = Notification.objects.create(
            recipient=recipient,
            message=f"{instance.author.username} just commented on your post: {instance.post.title}",
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
        )

        # # Push qua socket nếu online
        # async_to_sync(channel_layer.group_send)(
        #     f"notify_{recipient.id}",
        #     {
        #         "type": "notification_event",
        #         "data": {
        #             "message": notification.message,
        #             "timestamp": notification.created_at.isoformat(),
        #             "notification_id": notification.id,
        #         },
        #     }
        # )

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

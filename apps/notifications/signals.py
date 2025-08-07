from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@receiver(post_save, sender=Notification)
def send_realtime_notification(sender, instance, created, **kwargs):
    if not created:
        return

    channel_layer = get_channel_layer()
    group_name = f"notify_{instance.recipient.id}"

    # Nếu content_object tồn tại, lấy thêm thông tin
    target_type = instance.content_type.model if instance.content_type else None
    object_id = instance.object_id if instance.object_id else None

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "notification_event",
            "data": {
                "id": instance.id,
                "message": instance.message,
                "timestamp": instance.created_at.isoformat(),
                "is_read": instance.is_read,
                "target_type": target_type,
                "object_id": object_id,
            }
        }
    )

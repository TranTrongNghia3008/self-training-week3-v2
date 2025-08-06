import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# CELERY_BEAT_SCHEDULE = {
#     "publish_scheduled_posts_every_minute": {
#         "task": "apps.blog.tasks.publish_scheduled_posts",
#         "schedule": crontab(minute="*/1"), 
#     },
# }
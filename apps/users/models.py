from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    failed_login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username

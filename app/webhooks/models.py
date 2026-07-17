from django.db import models
from django.conf import settings
from core.constants import EVENT_CHOICES


class Webhook(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    url = models.URLField()
    event_type = models.CharField(max_length=100, choices=EVENT_CHOICES)
    secret = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.url} ({self.event_type})"

from django.db import models
from core.constants import EVENT_CHOICES

class Event(models.Model):
    event_type = models.CharField(max_length=100, choices=EVENT_CHOICES)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.event_type

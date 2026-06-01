from django.db import models
from app.webhooks.models import Webhook
from app.events.models import Event


class Delivery(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    response_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(null=True, blank=True)

    attempt_count = models.IntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("webhook", "event")]

    def __str__(self):
        return f"Delivery {self.id} -> {self.status}"

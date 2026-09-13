from django.conf import settings
from django.db import models

from core.constants import EVENT_CHOICES


class Webhook(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    url = models.URLField()
    event_type = models.CharField(max_length=100, choices=EVENT_CHOICES)
    # Stores a Fernet-encrypted ciphertext, never the plaintext secret.
    # Use core.utils.encrypt_secret()/decrypt_secret() to read or write it —
    # never assign this field directly. 512 chars comfortably fits an
    # encrypted token for secrets up to a few hundred characters long.
    secret = models.CharField(max_length=512)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Required for stable pagination — without a deterministic order,
        # Postgres can return the same row twice (or skip one) across
        # pages of the same paginated list.
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.url} ({self.event_type})"

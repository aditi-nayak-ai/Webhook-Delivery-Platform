from rest_framework import serializers
from .models import Webhook


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = "__all__"
        read_only_fields = ["user"]
        extra_kwargs = {
            # Never echo the HMAC secret back over the API — it's the key
            # external services use to verify signatures.
            "secret": {"write_only": True},
        }

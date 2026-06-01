from rest_framework import serializers
from .models import Delivery
 
 
class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = [
            "id",
            "webhook",
            "event",
            "status",
            "response_code",
            "response_body",
            "attempt_count",
            "last_attempt_at",
            "created_at",
        ]
        read_only_fields = fields
 

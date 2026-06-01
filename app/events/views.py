from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Event
from .serializers import EventSerializer
from app.webhooks.models import Webhook
from app.deliveries.tasks import send_webhook_task


class EventCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EventSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        event = serializer.save()

        webhooks = Webhook.objects.filter(
            event_type=event.event_type,
            is_active=True,
        )

        for webhook in webhooks:
            send_webhook_task.delay(webhook.id, event.id)

        return Response(
            {"message": "Event created and queued", "event_id": event.id},
            status=status.HTTP_201_CREATED,
        )

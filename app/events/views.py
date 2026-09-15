import logging
 
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
 
from app.deliveries.tasks import send_webhook_task
from app.webhooks.models import Webhook
 
from .serializers import EventSerializer
 
logger = logging.getLogger(__name__)
 
 
class EventCreateView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        serializer = EventSerializer(data=request.data)
 
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
        event = serializer.save()
 
        # Scoped to the requesting user — without this, any authenticated
        # user could trigger deliveries to every other user's registered
        # webhook endpoints just by guessing an event_type.
        webhooks = Webhook.objects.filter(
            event_type=event.event_type,
            is_active=True,
            user=request.user,
        )
 
        queue_failures = 0
        for webhook in webhooks:
            try:
                send_webhook_task.delay(webhook.id, event.id)
            except Exception:
                # A broker hiccup shouldn't turn an already-persisted event
                # into a 500 for the client. Log it; the event still exists
                # and can be redelivered/retried out of band.
                logger.exception(
                    "Failed to queue send_webhook_task for webhook_id=%s event_id=%s",
                    webhook.id, event.id,
                )
                queue_failures += 1
 
        response_data = {"message": "Event created and queued", "event_id": event.id}
        if queue_failures:
            response_data["message"] = "Event created, but some webhook deliveries failed to queue"
            response_data["queue_failures"] = queue_failures
 
        return Response(response_data, status=status.HTTP_201_CREATED)

from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from .models import Delivery
from .serializers import DeliverySerializer
 
 
class DeliveryListView(ListAPIView):
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]
 
    def get_queryset(self):
        # Scope deliveries to webhooks owned by the requesting user.
        # Without this, any authenticated user could read every delivery log.
        return Delivery.objects.filter(
            webhook__user=self.request.user
        ).select_related("webhook", "event").order_by("-created_at")

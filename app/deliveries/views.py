from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Delivery
from .serializers import DeliverySerializer


class DeliveryListView(ListAPIView):
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]
    # Lets clients narrow a growing delivery log, e.g.
    # /api/deliveries/?status=failed&webhook=3
    filterset_fields = ["status", "webhook", "event"]

    def get_queryset(self):
        return Delivery.objects.filter(
            webhook__user=self.request.user
        ).select_related("webhook", "event").order_by("-created_at")

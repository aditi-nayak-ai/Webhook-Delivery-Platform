from django.urls import path
from .views import DeliveryListView

urlpatterns = [
    path("", DeliveryListView.as_view(), name="delivery-list"),
]

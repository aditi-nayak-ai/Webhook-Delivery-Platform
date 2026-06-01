from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WebhookViewSet
 
router = DefaultRouter()
router.register(r"", WebhookViewSet, basename="webhook")
 
urlpatterns = [
    path("", include(router.urls)),
]
 

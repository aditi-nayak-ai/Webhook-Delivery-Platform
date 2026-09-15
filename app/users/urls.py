from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PublicTokenObtainPairView, PublicTokenRefreshView, UserViewSet

router = DefaultRouter()
router.register(r"", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
    path("token/", PublicTokenObtainPairView.as_view(), name="token-obtain"),
    path("token/refresh/", PublicTokenRefreshView.as_view(), name="token-refresh"),
]

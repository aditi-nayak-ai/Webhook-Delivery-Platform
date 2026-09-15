from rest_framework import permissions, viewsets
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import User
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return User.objects.order_by("id")
        return User.objects.filter(pk=user.pk).order_by("id")


class PublicTokenObtainPairView(TokenObtainPairView):
    """Login must be reachable without already being logged in -- the
    stock TokenObtainPairView doesn't set its own permission_classes, so
    it silently inherits the project's global DEFAULT_PERMISSION_CLASSES
    (IsAuthenticated), creating an impossible login-requires-login loop."""
    permission_classes = [AllowAny]


class PublicTokenRefreshView(TokenRefreshView):
    """Same rationale as PublicTokenObtainPairView above."""
    permission_classes = [AllowAny]

from rest_framework import viewsets, permissions
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
            return User.objects.all()
        return User.objects.filter(pk=user.pk)

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User
from .serializers import UserSerializer
 
 
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
 
    def get_permissions(self):
        # Registration must be open, everything else requires authentication.
        # The original used AllowAny for all actions — that means any anonymous
        # caller could list all users, update them, or delete them.
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
 
    def get_queryset(self):
        user = self.request.user
        # Non-admin users can only see themselves.
        if user.role == "admin":
            return User.objects.all()
        return User.objects.filter(pk=user.pk)

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserViewSet
 
router = DefaultRouter()
router.register(r"", UserViewSet, basename="user")
 
urlpatterns = [
    path("", include(router.urls)),
    path("token/", TokenObtainPairView.as_view(), name="token-obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
 

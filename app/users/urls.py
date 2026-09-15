from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
 
from .views import UserViewSet
 
router = DefaultRouter()
router.register(r"", UserViewSet, basename="user")
 
urlpatterns = [
    # These must come before the router include: DefaultRouter's detail
    # route (r"^(?P<pk>[^/.]+)/$") on an empty prefix would otherwise
    # swallow "token/" and "token/refresh/" as a pk lookup first, since
    # Django matches urlpatterns in order.
    path("token/", TokenObtainPairView.as_view(), name="token-obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("", include(router.urls)),
]
 

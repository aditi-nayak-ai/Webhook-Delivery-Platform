from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def home(request):
    return JsonResponse({"status": "API is running"})


urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/users/", include("app.users.urls")),
    path("api/events/", include("app.events.urls")),
    path("api/deliveries/", include("app.deliveries.urls")),
    path("api/webhooks/", include("app.webhooks.urls")),
]

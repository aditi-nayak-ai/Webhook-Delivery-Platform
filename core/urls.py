from django.http import JsonResponse

urlpatterns = [
    path("", lambda request: JsonResponse({"status": "API is running"})),

    path("admin/", admin.site.urls),
    path("api/users/", include("app.users.urls")),
    path("api/events/", include("app.events.urls")),
    path("api/deliveries/", include("app.deliveries.urls")),
    path("api/webhooks/", include("app.webhooks.urls")),
]

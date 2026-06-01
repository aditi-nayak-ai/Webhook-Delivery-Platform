from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html")),
    path("admin/", admin.site.urls),
    path("api/users/", include("app.users.urls")),
    path("api/events/", include("app.events.urls")),
    path("api/deliveries/", include("app.deliveries.urls")),
    path("api/webhooks/", include("app.webhooks.urls")),
]

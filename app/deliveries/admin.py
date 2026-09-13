from django.contrib import admin

from .models import Delivery


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "id", "webhook", "event", "status", "response_code",
        "attempt_count", "last_attempt_at",
    )
    list_filter = ("status",)
    readonly_fields = [f.name for f in Delivery._meta.fields]

    def has_add_permission(self, request):
        # Deliveries are only ever created by send_webhook_task — never
        # by a human clicking "Add" in the admin.
        return False

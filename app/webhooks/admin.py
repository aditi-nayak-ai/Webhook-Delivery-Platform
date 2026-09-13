from django.contrib import admin

from .models import Webhook


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "url", "event_type", "is_active", "created_at")
    list_filter = ("event_type", "is_active")
    search_fields = ("url", "user__username")
    # Never surface the encrypted secret in the admin — there's no
    # legitimate reason for a support/ops user to see it, encrypted or not.
    exclude = ("secret",)
    readonly_fields = ("created_at",)

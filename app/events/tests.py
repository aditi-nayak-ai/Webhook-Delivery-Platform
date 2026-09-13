from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from app.users.models import User
from app.webhooks.models import Webhook
from core.utils import encrypt_secret

from .models import Event

VALID_SECRET = "a-sufficiently-long-secret-value"


class EventCreateViewTests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="a", password="pass12345")
        self.user_b = User.objects.create_user(username="b", password="pass12345")

        self.webhook_a = Webhook.objects.create(
            user=self.user_a, url="https://example.com/hook-a",
            event_type="payment.success", secret=encrypt_secret(VALID_SECRET),
        )
        self.webhook_b = Webhook.objects.create(
            user=self.user_b, url="https://example.com/hook-b",
            event_type="payment.success", secret=encrypt_secret(VALID_SECRET),
        )

    @patch("app.events.views.send_webhook_task")
    def test_event_only_dispatches_to_the_requesting_users_webhooks(self, mock_task):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post("/api/events/", {
            "event_type": "payment.success",
            "payload": {"amount": 100},
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        event_id = response.data["event_id"]

        mock_task.delay.assert_called_once_with(self.webhook_a.id, event_id)

    @patch("app.events.views.send_webhook_task")
    def test_inactive_webhook_is_not_dispatched(self, mock_task):
        self.webhook_a.is_active = False
        self.webhook_a.save(update_fields=["is_active"])

        self.client.force_authenticate(user=self.user_a)
        self.client.post("/api/events/", {
            "event_type": "payment.success",
            "payload": {"amount": 100},
        }, format="json")

        mock_task.delay.assert_not_called()

    def test_invalid_event_type_is_rejected(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post("/api/events/", {
            "event_type": "not.a.real.type",
            "payload": {},
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.post("/api/events/", {
            "event_type": "payment.success",
            "payload": {},
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("app.events.views.send_webhook_task")
    def test_event_is_persisted(self, mock_task):
        self.client.force_authenticate(user=self.user_a)
        self.client.post("/api/events/", {
            "event_type": "payment.success",
            "payload": {"amount": 250},
        }, format="json")
        self.assertEqual(Event.objects.filter(event_type="payment.success").count(), 1)

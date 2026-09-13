"""Tests for EventCreateView.

The most important behavior here isn't event creation itself -- it's that
publishing an event only queues deliveries to the AUTHENTICATED USER's own
webhooks. Without that scoping, any user could trigger deliveries to every
other user's registered endpoints just by knowing (or guessing) an
event_type -- see the comment in views.py this test pins down.
"""

from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from app.events.models import Event
from app.users.models import User
from app.webhooks.models import Webhook


class EventCreateViewTests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="a", password="pass12345")
        self.user_b = User.objects.create_user(username="b", password="pass12345")
        self.url = reverse("event-create")

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.post(self.url, {
            "event_type": "payment.success",
            "payload": {"amount": 1000},
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_payload_returns_400(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(self.url, {
            "event_type": "",  # blank -- not a valid choice
            "payload": {"amount": 1000},
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("app.events.views.send_webhook_task.delay")
    def test_event_creation_succeeds_with_no_matching_webhooks(self, mock_delay):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(self.url, {
            "event_type": "payment.success",
            "payload": {"amount": 1000},
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Event.objects.filter(event_type="payment.success").exists())
        mock_delay.assert_not_called()

    @patch("app.events.views.send_webhook_task.delay")
    def test_event_only_queues_deliveries_to_the_publishing_users_own_webhooks(self, mock_delay):
        """Core security guarantee: user_b's webhook must NEVER be queued
        for an event user_a publishes, even though both are registered
        for the exact same event_type."""
        Webhook.objects.create(
            user=self.user_a, url="https://example.com/a-hook",
            event_type="payment.success", secret="secret-a",
        )
        Webhook.objects.create(
            user=self.user_b, url="https://example.com/b-hook",
            event_type="payment.success", secret="secret-b",
        )

        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(self.url, {
            "event_type": "payment.success",
            "payload": {"amount": 1000},
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_delay.assert_called_once()
        # The only webhook.delay() call must be for user_a's webhook.
        called_webhook_id = mock_delay.call_args.args[0]
        self.assertEqual(
            called_webhook_id,
            Webhook.objects.get(user=self.user_a).id,
        )

    @patch("app.events.views.send_webhook_task.delay")
    def test_inactive_webhooks_are_not_queued(self, mock_delay):
        Webhook.objects.create(
            user=self.user_a, url="https://example.com/a-hook",
            event_type="payment.success", secret="secret-a",
            is_active=False,
        )
        self.client.force_authenticate(user=self.user_a)
        self.client.post(self.url, {
            "event_type": "payment.success",
            "payload": {"amount": 1000},
        }, format="json")
        mock_delay.assert_not_called()

    @patch("app.events.views.send_webhook_task.delay")
    def test_mismatched_event_type_webhooks_are_not_queued(self, mock_delay):
        Webhook.objects.create(
            user=self.user_a, url="https://example.com/a-hook",
            event_type="user.created", secret="secret-a",
        )
        self.client.force_authenticate(user=self.user_a)
        self.client.post(self.url, {
            "event_type": "payment.success",
            "payload": {"amount": 1000},
        }, format="json")
        mock_delay.assert_not_called()

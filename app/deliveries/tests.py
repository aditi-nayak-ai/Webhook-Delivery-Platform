from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError

from app.events.models import Event
from app.users.models import User
from app.webhooks.models import Webhook
from core.utils import decrypt_secret, encrypt_secret

from .models import Delivery
from .tasks import send_webhook_task


def _make_response(status_code, body="ok"):
    response = MagicMock()
    response.status_code = status_code
    response.text = body
    if status_code >= 400:
        response.raise_for_status.side_effect = HTTPError(response=response)
    else:
        response.raise_for_status.side_effect = None
    return response


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class SendWebhookTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dev", password="pass12345")
        self.webhook = Webhook.objects.create(
            user=self.user,
            url="https://example.com/hook",
            event_type="payment.success",
            secret=encrypt_secret("super-secret-value"),
        )
        self.event = Event.objects.create(
            event_type="payment.success",
            payload={"amount": 500, "currency": "usd"},
        )

    @patch("app.deliveries.tasks.requests.post")
    def test_success_marks_delivery_successful(self, mock_post):
        mock_post.return_value = _make_response(200)

        send_webhook_task.apply(args=(self.webhook.id, self.event.id))

        delivery = Delivery.objects.get(webhook=self.webhook, event=self.event)
        self.assertEqual(delivery.status, "success")
        self.assertEqual(delivery.response_code, 200)
        self.assertEqual(delivery.attempt_count, 1)
        self.assertIsNotNone(delivery.last_attempt_at)

    @patch("app.deliveries.tasks.requests.post")
    def test_signature_is_generated_from_decrypted_secret_not_ciphertext(self, mock_post):
        mock_post.return_value = _make_response(200)

        send_webhook_task.apply(args=(self.webhook.id, self.event.id))

        sent_headers = mock_post.call_args.kwargs["headers"]
        self.assertIn("X-Webhook-Signature", sent_headers)
        self.assertNotEqual(decrypt_secret(self.webhook.secret), self.webhook.secret)

    @patch("app.deliveries.tasks.requests.post")
    def test_permanent_4xx_does_not_retry(self, mock_post):
        mock_post.return_value = _make_response(404, body="not found")

        send_webhook_task.apply(args=(self.webhook.id, self.event.id))

        delivery = Delivery.objects.get(webhook=self.webhook, event=self.event)
        self.assertEqual(delivery.status, "failed")
        self.assertEqual(delivery.response_code, 404)
        self.assertEqual(delivery.attempt_count, 1)

    @patch("app.deliveries.tasks.requests.post")
    def test_429_is_retried_unlike_other_4xx(self, mock_post):
        mock_post.return_value = _make_response(429, body="rate limited")

        send_webhook_task.apply(args=(self.webhook.id, self.event.id))

        delivery = Delivery.objects.get(webhook=self.webhook, event=self.event)
        self.assertEqual(delivery.status, "failed")
        self.assertEqual(delivery.attempt_count, 4)

    @patch("app.deliveries.tasks.requests.post")
    def test_5xx_is_retried_and_exhausts_max_retries(self, mock_post):
        mock_post.return_value = _make_response(503, body="upstream down")

        send_webhook_task.apply(args=(self.webhook.id, self.event.id))

        delivery = Delivery.objects.get(webhook=self.webhook, event=self.event)
        self.assertEqual(delivery.status, "failed")
        self.assertEqual(delivery.attempt_count, 4)

    @patch("app.deliveries.tasks.requests.post")
    def test_connection_error_is_retried(self, mock_post):
        mock_post.side_effect = RequestsConnectionError("connection refused")

        send_webhook_task.apply(args=(self.webhook.id, self.event.id))

        delivery = Delivery.objects.get(webhook=self.webhook, event=self.event)
        self.assertEqual(delivery.status, "failed")
        self.assertIn("connection refused", delivery.response_body)
        self.assertEqual(delivery.attempt_count, 4)

    def test_deleted_event_is_skipped_without_raising(self):
        deleted_event_id = self.event.id
        self.event.delete()

        send_webhook_task.apply(args=(self.webhook.id, deleted_event_id))

        self.assertFalse(Delivery.objects.filter(webhook=self.webhook).exists())

    @patch("app.deliveries.tasks.requests.post")
    def test_concurrent_deliveries_do_not_duplicate_rows(self, mock_post):
        mock_post.return_value = _make_response(200)

        send_webhook_task.apply(args=(self.webhook.id, self.event.id))
        send_webhook_task.apply(args=(self.webhook.id, self.event.id))

        self.assertEqual(
            Delivery.objects.filter(webhook=self.webhook, event=self.event).count(), 1,
        )
        delivery = Delivery.objects.get(webhook=self.webhook, event=self.event)
        self.assertEqual(delivery.attempt_count, 2)

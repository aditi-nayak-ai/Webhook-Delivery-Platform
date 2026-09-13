"""Tests for send_webhook_task -- the actual delivery/retry/signing logic.

Run with CELERY_TASK_ALWAYS_EAGER=True (see setUp) so the task executes
synchronously in-process, no real Redis broker needed. Outbound HTTP
(requests.post) is mocked in every test -- these tests verify OUR retry,
signing, and status-tracking logic, not whether the internet works.
"""

import hashlib
import hmac
import json
from unittest.mock import Mock, patch

from celery.exceptions import Retry
from django.test import TestCase, override_settings

from app.deliveries.models import Delivery
from app.deliveries.tasks import send_webhook_task
from app.events.models import Event
from app.users.models import User
from app.webhooks.models import Webhook


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class SendWebhookTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass12345")
        self.webhook = Webhook.objects.create(
            user=self.user,
            url="https://example.com/hook",
            event_type="payment.success",
            secret="test-secret",
        )
        self.event = Event.objects.create(
            event_type="payment.success",
            payload={"amount": 1000, "currency": "INR"},
        )

    @patch("app.deliveries.tasks.requests.post")
    def test_successful_delivery_marks_status_success(self, mock_post):
        mock_post.return_value = Mock(status_code=200, text="OK")
        mock_post.return_value.raise_for_status = Mock()  # 2xx -> no raise

        send_webhook_task.apply(args=(self.webhook.id, self.event.id))

        delivery = Delivery.objects.get(webhook=self.webhook, event=self.event)
        self.assertEqual(delivery.status, "success")
        self.assertEqual(delivery.response_code, 200)
        self.assertEqual(delivery.attempt_count, 1)
        self.assertIsNotNone(delivery.last_attempt_at)

    @patch("app.deliveries.tasks.requests.post")
    def test_signature_header_is_correct_hmac_sha256(self, mock_post):
        """The receiving service verifies this signature -- it must match
        exactly what core.utils.generate_signature would independently
        compute for the same payload+secret, or every real integration
        would silently reject every delivery."""
        mock_post.return_value = Mock(status_code=200, text="OK")
        mock_post.return_value.raise_for_status = Mock()

        send_webhook_task.apply(args=(self.webhook.id, self.event.id))

        sent_headers = mock_post.call_args.kwargs["headers"]
        expected_signature = hmac.new(
            key=self.webhook.secret.encode(),
            msg=json.dumps(self.event.payload, separators=(",", ":")).encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()
        self.assertEqual(sent_headers["X-Webhook-Signature"], expected_signature)

    @patch("app.deliveries.tasks.requests.post")
    def test_delivery_sends_the_event_payload_as_json_body(self, mock_post):
        mock_post.return_value = Mock(status_code=200, text="OK")
        mock_post.return_value.raise_for_status = Mock()

        send_webhook_task.apply(args=(self.webhook.id, self.event.id))

        sent_json = mock_post.call_args.kwargs["json"]
        self.assertEqual(sent_json, self.event.payload)

    @patch("app.deliveries.tasks.requests.post")
    def test_http_error_response_marks_status_failed_and_retries(self, mock_post):
        """A non-2xx response (raise_for_status) is a distinct failure
        path from a network-level exception (DNS, timeout, connection
        refused) -- both must still retry, but this confirms the
        HTTPError branch specifically records the real response code
        before retrying, not just a generic failure."""
        import requests as requests_module

        mock_response = Mock(status_code=500, text="Internal Server Error")
        mock_response.raise_for_status.side_effect = requests_module.exceptions.HTTPError(
            response=mock_response
        )
        mock_post.return_value = mock_response

        with self.assertRaises(Retry):
            send_webhook_task.apply(args=(self.webhook.id, self.event.id), throw=True)

        delivery = Delivery.objects.get(webhook=self.webhook, event=self.event)
        self.assertEqual(delivery.status, "failed")
        self.assertEqual(delivery.response_code, 500)
        self.assertGreaterEqual(delivery.attempt_count, 1)

    @patch("app.deliveries.tasks.requests.post")
    def test_connection_error_marks_status_failed_and_retries(self, mock_post):
        """A network-level exception (no response at all) must be caught
        by the broad except-Exception branch, not left unhandled -- an
        unhandled exception here would crash the worker process instead
        of retrying the delivery."""
        import requests as requests_module

        mock_post.side_effect = requests_module.exceptions.ConnectionError("DNS resolution failed")

        with self.assertRaises(Retry):
            send_webhook_task.apply(args=(self.webhook.id, self.event.id), throw=True)

        delivery = Delivery.objects.get(webhook=self.webhook, event=self.event)
        self.assertEqual(delivery.status, "failed")
        self.assertIn("DNS resolution failed", delivery.response_body)

    @patch("app.deliveries.tasks.requests.post")
    def test_attempt_count_increments_on_repeated_calls(self, mock_post):
        """Simulates the same (webhook, event) pair being processed
        across multiple retry cycles -- get_or_create means the same
        Delivery row is reused, and attempt_count must accumulate rather
        than resetting each time."""
        mock_post.return_value = Mock(status_code=200, text="OK")
        mock_post.return_value.raise_for_status = Mock()

        send_webhook_task.apply(args=(self.webhook.id, self.event.id))
        send_webhook_task.apply(args=(self.webhook.id, self.event.id))

        delivery = Delivery.objects.get(webhook=self.webhook, event=self.event)
        self.assertEqual(delivery.attempt_count, 2)

    @patch("app.deliveries.tasks.requests.post")
    def test_response_body_is_truncated_to_1000_chars(self, mock_post):
        """Unbounded response bodies (a receiver echoing back a huge
        payload, or an error page) shouldn't be stored in full -- see
        the [:1000] slice in tasks.py."""
        mock_post.return_value = Mock(status_code=200, text="x" * 5000)
        mock_post.return_value.raise_for_status = Mock()

        send_webhook_task.apply(args=(self.webhook.id, self.event.id))

        delivery = Delivery.objects.get(webhook=self.webhook, event=self.event)
        self.assertEqual(len(delivery.response_body), 1000)

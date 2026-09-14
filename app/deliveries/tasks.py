from django.test import TestCase
from app.users.models import User
from app.webhooks.models import Webhook
from app.events.models import Event
from app.deliveries.models import Delivery
from app.deliveries.tasks import send_webhook_task
from core.utils import encrypt_secret
from unittest.mock import patch

class WebhookDeliveryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")
        
        # Plaintext ki jagah encrypt_secret() use hona chahiye
        self.webhook = Webhook.objects.create(
            user=self.user,
            url="https://example.com/webhook",
            event_type="order.created",
            secret=encrypt_secret("test-secret-at-least-16-chars")
        )
        self.event = Event.objects.create(
            event_type="order.created",
            payload={"id": 1, "status": "completed"}
        )

    @patch("requests.post")
    def test_send_webhook_task_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "OK"

        send_webhook_task.apply(args=[self.webhook.id, self.event.id])

        delivery = Delivery.objects.get(webhook=self.webhook, event=self.event)
        self.assertEqual(delivery.status, "success")
        self.assertEqual(delivery.response_code, 200)

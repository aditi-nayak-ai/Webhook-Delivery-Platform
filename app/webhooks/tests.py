from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from app.users.models import User
from app.webhooks.models import Webhook


class WebhookScopingTests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="a", password="pass12345")
        self.user_b = User.objects.create_user(username="b", password="pass12345")
        self.webhook_a = Webhook.objects.create(
            user=self.user_a, url="https://example.com/hook",
            event_type="payment.success", secret="secret123",
        )

    def test_user_cannot_see_other_users_webhooks(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.get("/api/webhooks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_webhook_rejects_private_ip_target(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post("/api/webhooks/", {
            "url": "http://169.254.169.254/latest/meta-data/",
            "event_type": "payment.success",
            "secret": "secret123",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_webhook_accepts_public_url(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post("/api/webhooks/", {
            "url": "https://example.com/hook",
            "event_type": "user.created",
            "secret": "secret123",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

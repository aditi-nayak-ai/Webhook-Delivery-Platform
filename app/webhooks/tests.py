from rest_framework import status
from rest_framework.test import APITestCase

from app.users.models import User
from core.utils import encrypt_secret

from .models import Webhook

VALID_SECRET = "a-sufficiently-long-secret-value"


class WebhookScopingTests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="a", password="pass12345")
        self.user_b = User.objects.create_user(username="b", password="pass12345")
        self.webhook_a = Webhook.objects.create(
            user=self.user_a, url="https://example.com/hook",
            event_type="payment.success", secret=encrypt_secret(VALID_SECRET),
        )

    def test_user_cannot_see_other_users_webhooks(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.get("/api/webhooks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_webhook_rejects_private_ip_target(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post("/api/webhooks/", {
            "url": "http://169.254.169.254/latest/meta-data/",
            "event_type": "payment.success",
            "secret": VALID_SECRET,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("url", response.data)

    def test_webhook_accepts_public_url(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post("/api/webhooks/", {
            "url": "https://example.com/hook",
            "event_type": "user.created",
            "secret": VALID_SECRET,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_secret_is_never_returned_in_response(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(f"/api/webhooks/{self.webhook_a.id}/")
        self.assertNotIn("secret", response.data)

    def test_secret_is_encrypted_at_rest(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post("/api/webhooks/", {
            "url": "https://example.com/hook2",
            "event_type": "user.created",
            "secret": VALID_SECRET,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        stored = Webhook.objects.get(id=response.data["id"])
        # The raw DB value must never equal the plaintext the client sent.
        self.assertNotEqual(stored.secret, VALID_SECRET)

    def test_short_secret_is_rejected(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post("/api/webhooks/", {
            "url": "https://example.com/hook3",
            "event_type": "user.created",
            "secret": "tooshort",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("secret", response.data)

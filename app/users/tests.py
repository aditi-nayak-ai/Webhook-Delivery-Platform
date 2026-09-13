from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class UserRegistrationTests(APITestCase):
    def test_registration_does_not_require_authentication(self):
        response = self.client.post("/api/users/", {
            "username": "newdev",
            "password": "pass12345",
            "email": "newdev@example.com",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_registration_ignores_client_supplied_role(self):
        response = self.client.post("/api/users/", {
            "username": "sneaky",
            "password": "pass12345",
            "role": "admin",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="sneaky")
        self.assertEqual(user.role, "developer")

    def test_password_is_hashed_not_stored_in_plaintext(self):
        self.client.post("/api/users/", {
            "username": "hashcheck",
            "password": "pass12345",
        })
        user = User.objects.get(username="hashcheck")
        self.assertNotEqual(user.password, "pass12345")

    def test_password_is_never_returned_in_response(self):
        response = self.client.post("/api/users/", {
            "username": "nopassback",
            "password": "pass12345",
        })
        self.assertNotIn("password", response.data)


class UserVisibilityTests(APITestCase):
    def setUp(self):
        self.developer = User.objects.create_user(
            username="dev", password="pass12345", role="developer",
        )
        self.admin = User.objects.create_user(
            username="admin", password="pass12345", role="admin",
        )

    def test_developer_only_sees_self(self):
        self.client.force_authenticate(user=self.developer)
        response = self.client.get("/api/users/")
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["username"], "dev")

    def test_admin_sees_all_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/users/")
        self.assertEqual(len(response.data["results"]), 2)

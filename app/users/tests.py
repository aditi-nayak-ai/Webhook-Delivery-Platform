from rest_framework import status
from rest_framework.test import APITestCase

from app.users.models import User


class UserRegistrationTests(APITestCase):
    def setUp(self):
        self.url = "/api/users/"

    def test_anyone_can_register_without_auth(self):
        response = self.client.post(self.url, {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "pass12345",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_new_user_defaults_to_developer_role(self):
        """role is write-protected (read_only in the serializer) so a
        registration request can't self-elevate to admin by just adding
        "role": "admin" to the payload."""
        response = self.client.post(self.url, {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "pass12345",
            "role": "admin",  # attempted privilege escalation
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = User.objects.get(username="newuser")
        self.assertEqual(created.role, "developer")

    def test_registered_password_is_usable_for_login(self):
        """create_user() must be called (which hashes the password) --
        not a raw .create(), which would store it in plaintext and break
        every subsequent login."""
        self.client.post(self.url, {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "pass12345",
        })
        user = User.objects.get(username="newuser")
        self.assertTrue(user.check_password("pass12345"))

    def test_password_is_never_returned_in_the_response(self):
        response = self.client.post(self.url, {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "pass12345",
        })
        self.assertNotIn("password", response.data)


class UserQuerysetScopingTests(APITestCase):
    def setUp(self):
        self.developer = User.objects.create_user(
            username="dev", password="pass12345", role="developer"
        )
        self.other_developer = User.objects.create_user(
            username="dev2", password="pass12345", role="developer"
        )
        self.admin = User.objects.create_user(
            username="admin_user", password="pass12345", role="admin"
        )

    def test_developer_only_sees_themselves(self):
        self.client.force_authenticate(user=self.developer)
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = [u["username"] for u in response.data]
        self.assertEqual(usernames, ["dev"])

    def test_admin_sees_every_user(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = {u["username"] for u in response.data}
        self.assertEqual(usernames, {"dev", "dev2", "admin_user"})

    def test_unauthenticated_list_request_is_rejected(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

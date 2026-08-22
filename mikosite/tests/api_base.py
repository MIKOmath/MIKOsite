"""Shared fixtures for the API tests: one caller per access plane.

Not named `test_*`, so the runner collects it as a helper rather than a suite.
"""
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage
from rest_framework.test import APITestCase

from accounts.models import User

PASSWORD = 'Testpass1!'


def tiny_image(name='test.png') -> SimpleUploadedFile:
    """A real one-pixel PNG, because ImageField validation opens what it is given."""
    buffer = BytesIO()
    PILImage.new('RGB', (1, 1)).save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')

# Credentials. These must never appear as a key in an API response, on any
# plane, for any caller. Privilege flags are a separate matter - they are
# readable on the administrator plane, so `test_api_users` checks them per plane
# rather than globally.
FORBIDDEN_RESPONSE_KEYS = {
    'password',
    'auth_token',
    'token',
    'key',
}


def collect_keys(payload, found=None) -> set:
    """Every key appearing anywhere in a nested response body."""
    found = set() if found is None else found
    if isinstance(payload, dict):
        for key, value in payload.items():
            found.add(key)
            collect_keys(value, found)
    elif isinstance(payload, list):
        for item in payload:
            collect_keys(item, found)
    return found


class ApiPlaneTestCase(APITestCase):
    """Four callers, because the API distinguishes exactly four.

    `staff` earns its place by proving a negative: being staff is admin-panel
    access and buys nothing at all over the API.
    """

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username='admin', email='admin@test.com', password=PASSWORD,
        )
        cls.staff = User.objects.create_user(
            username='staffer', email='staff@test.com', password=PASSWORD, is_staff=True,
        )
        cls.member = User.objects.create_user(
            username='member', email='member@test.com', password=PASSWORD,
        )

    def as_admin(self):
        self.client.force_authenticate(self.admin)

    def as_staff(self):
        self.client.force_authenticate(self.staff)

    def as_member(self):
        self.client.force_authenticate(self.member)

    def as_anonymous(self):
        self.client.force_authenticate(None)

    def assertNoSecretsIn(self, payload, where):
        leaked = collect_keys(payload) & FORBIDDEN_RESPONSE_KEYS
        self.assertEqual(leaked, set(), f"{where} exposed {sorted(leaked)}")

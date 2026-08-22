"""Email change: pending until confirmed, cancellable, then the login email."""
import re

from django.core import mail
from django.core.cache import cache
from django.test import TestCase

from accounts.models import User
from allauth.account.models import EmailAddress

from .auth_base import PASSWORD, make_verified_user

EMAIL_URL = '/accounts/email/'
NEW_EMAIL = 'nowy@test.com'


class EmailChangeTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_verified_user()
        self.client.post('/accounts/login/', {'login': 'marek123', 'password': PASSWORD})

    def request_change(self):
        return self.client.post(EMAIL_URL, {'email': NEW_EMAIL, 'action_add': ''})

    def test_the_page_shows_the_current_address(self):
        response = self.client.get(EMAIL_URL)

        self.assertContains(response, 'marek@test.com')
        self.assertContains(response, 'Zmiana adresu email')

    def test_a_change_creates_a_pending_address_and_mails_it(self):
        self.request_change()

        pending = EmailAddress.objects.get(email=NEW_EMAIL)
        self.assertFalse(pending.verified)
        self.assertFalse(pending.primary)
        self.assertEqual(mail.outbox[-1].to, [NEW_EMAIL])

        response = self.client.get(EMAIL_URL)
        self.assertContains(response, 'Oczekuje na potwierdzenie')

    def test_the_old_address_keeps_working_until_confirmation(self):
        self.request_change()

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'marek@test.com')

    def test_the_pending_change_can_be_cancelled(self):
        self.request_change()

        self.client.post(EMAIL_URL, {'email': NEW_EMAIL, 'action_remove': ''})

        self.assertFalse(EmailAddress.objects.filter(email=NEW_EMAIL).exists())

    def test_confirming_makes_the_new_address_the_login_email(self):
        self.request_change()
        link = re.search(r'https?://[^\s]+/confirm-email/[^\s/]+/', mail.outbox[-1].body)
        self.assertIsNotNone(link)
        path = '/' + link.group(0).split('://', 1)[-1].split('/', 1)[-1]

        self.client.post(path)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, NEW_EMAIL)
        self.assertFalse(EmailAddress.objects.filter(email='marek@test.com').exists())

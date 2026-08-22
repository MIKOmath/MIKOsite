"""Password reset: relay-bound mail, enumeration-proof, claims unusable passwords."""
import re

from django.core import mail
from django.core.cache import cache
from django.test import TestCase

from accounts.models import User

from .auth_base import NEW_PASSWORD, TURNSTILE_FAIL, TURNSTILE_OK, make_verified_user

RESET_URL = '/accounts/password/reset/'
LOGIN_URL = '/accounts/login/'


class PasswordResetRequestTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_the_page_wears_the_house_shell_and_the_turnstile(self):
        response = self.client.get(RESET_URL)

        self.assertEqual(response.status_code, 200)
        for marker in ('auth-card', 'Reset hasła', 'cf-turnstile', 'data-action="reset"'):
            self.assertContains(response, marker)

    @TURNSTILE_OK
    def test_known_and_unknown_addresses_are_outwardly_identical(self, _):
        make_verified_user()

        known = self.client.post(RESET_URL, {'email': 'marek@test.com'})
        mails_for_known = len(mail.outbox)
        unknown = self.client.post(RESET_URL, {'email': 'nieistnieje@test.com'})
        mails_for_unknown = len(mail.outbox) - mails_for_known

        # Same redirect either way, and one email either way - a reset link for
        # the member, a "no account here" note for the stranger.
        self.assertEqual(known.headers['Location'], unknown.headers['Location'])
        self.assertEqual(mails_for_known, 1)
        self.assertEqual(mails_for_unknown, 1)

    @TURNSTILE_FAIL
    def test_a_failed_turnstile_sends_nothing(self, _):
        make_verified_user()

        response = self.client.post(RESET_URL, {'email': 'marek@test.com'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)


class PasswordResetCompletionTests(TestCase):
    def setUp(self):
        cache.clear()

    def reset_link_for(self, email):
        with TURNSTILE_OK:
            self.client.post(RESET_URL, {'email': email})
        body = mail.outbox[-1].body
        match = re.search(r'https?://[^\s]+/password/reset/key/[^\s]+', body)
        assert match, f"no reset link in mail body:\n{body}"
        return '/' + match.group(0).split('://', 1)[-1].split('/', 1)[-1]

    def set_new_password(self, link):
        landing = self.client.get(link, follow=True)
        form_url = landing.redirect_chain[-1][0] if landing.redirect_chain else link
        return self.client.post(
            form_url, {'password1': NEW_PASSWORD, 'password2': NEW_PASSWORD}, follow=True,
        )

    def test_the_mailed_link_sets_a_new_password(self):
        make_verified_user()
        link = self.reset_link_for('marek@test.com')

        self.set_new_password(link)

        user = User.objects.get(username='marek123')
        self.assertTrue(user.check_password(NEW_PASSWORD))

        response = self.client.post(LOGIN_URL, {'login': 'marek123', 'password': NEW_PASSWORD})
        self.assertEqual(response.headers['Location'], '/')

    def test_a_used_link_is_refused_the_second_time(self):
        make_verified_user()
        link = self.reset_link_for('marek@test.com')
        self.set_new_password(link)

        response = self.client.get(link, follow=True)

        self.assertContains(response, "nieprawidłowy")

    def test_an_account_without_a_usable_password_can_claim_one(self):
        """API-created accounts carry set_unusable_password(); the reset flow is
        exactly how such an account first gets a password."""
        user = make_verified_user()
        user.set_unusable_password()
        user.save()

        link = self.reset_link_for('marek@test.com')
        self.set_new_password(link)

        user.refresh_from_db()
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.check_password(NEW_PASSWORD))

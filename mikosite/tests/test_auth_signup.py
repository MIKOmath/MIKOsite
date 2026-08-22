"""Local signup: Turnstile-gated, extras collected, email verified before login."""
from datetime import date
from django.core import mail
from django.core.cache import cache
from django.test import TestCase

from accounts.models import User
from allauth.account.models import EmailAddress

from .auth_base import TURNSTILE_FAIL, TURNSTILE_OK

SIGNUP_URL = '/accounts/signup/'
LOGIN_URL = '/accounts/login/'


def signup_payload(**overrides):
    payload = {
        'username': 'marek123',
        'email': 'marek@test.com',
        'password1': 'Correct1!horse',
        'password2': 'Correct1!horse',
        'first_name': 'Marek',
        'last_name': 'Testowy',
        'region': 'MZ',
        'date_of_birth': '2005-01-01',
    }
    payload.update(overrides)
    return payload


class SignupPageTests(TestCase):
    def test_the_page_wears_the_house_shell(self):
        response = self.client.get(SIGNUP_URL)

        self.assertEqual(response.status_code, 200)
        for marker in ('auth-card', 'Rejestracja', 'cf-turnstile', 'turnstile/v0/api.js',
                       'password-rules', 'first_name', 'region', 'date_of_birth'):
            self.assertContains(response, marker)

    def test_the_old_address_still_arrives_here(self):
        response = self.client.get('/signup/')

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers['Location'], SIGNUP_URL)


class SignupFlowTests(TestCase):
    def setUp(self):
        # Allauth cooldowns live in the cache, which outlives a test.
        cache.clear()
        # Not zero: the about-page cards arrive with placeholder accounts of
        # their own. What these tests watch is whether signup adds to the roll.
        self.accounts_before = User.objects.count()

    @TURNSTILE_OK
    def test_signup_creates_the_account_with_its_extras(self, _):
        response = self.client.post(SIGNUP_URL, signup_payload())

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='marek123')
        self.assertEqual(user.first_name, 'Marek')
        self.assertEqual(user.region, 'MZ')
        self.assertEqual(user.date_of_birth, date(2005, 1, 1))

    @TURNSTILE_OK
    def test_signup_sends_the_verification_mail_and_gates_login(self, _):
        self.client.post(SIGNUP_URL, signup_payload())

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('marek@test.com', mail.outbox[0].to)
        self.assertTrue(mail.outbox[0].subject.startswith('[MIKO] '))
        self.assertIn('zespół MIKO', mail.outbox[0].body)
        address = EmailAddress.objects.get(email='marek@test.com')
        self.assertFalse(address.verified)

        # An unverified account cannot get past the login view.
        response = self.client.post(
            LOGIN_URL, {'login': 'marek123', 'password': 'Correct1!horse'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('confirm-email', response.headers['Location'])

    @TURNSTILE_OK
    def test_the_mailed_link_verifies_and_unlocks_login(self, _):
        self.client.post(SIGNUP_URL, signup_payload())
        confirm_url = next(
            line for line in mail.outbox[0].body.splitlines() if 'confirm-email' in line
        ).strip()
        confirm_path = confirm_url.split('://', 1)[-1].split('/', 1)[-1]

        page = self.client.get(f'/{confirm_path}')
        self.assertEqual(page.status_code, 200)
        self.client.post(f'/{confirm_path}')

        self.assertTrue(EmailAddress.objects.get(email='marek@test.com').verified)
        response = self.client.post(
            LOGIN_URL, {'login': 'marek123', 'password': 'Correct1!horse'},
        )
        self.assertEqual(response.headers['Location'], '/')

    @TURNSTILE_OK
    def test_signup_with_a_taken_email_neither_errors_nor_creates(self, _):
        User.objects.create_user(username='istnieje', email='marek@test.com', password='Xx1!aaaaaa')

        response = self.client.post(SIGNUP_URL, signup_payload(username='ktosinny'))

        # Outwardly identical to a successful signup...
        self.assertEqual(response.status_code, 302)
        # ...but no account appears, and the address holder is told by mail.
        self.assertFalse(User.objects.filter(username='ktosinny').exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('marek@test.com', mail.outbox[0].to)

    @TURNSTILE_FAIL
    def test_a_failed_turnstile_blocks_the_signup(self, _):
        response = self.client.post(SIGNUP_URL, signup_payload())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Potwierdź, że nie jesteś botem.")
        self.assertFalse(User.objects.filter(username='marek123').exists())

    @TURNSTILE_OK
    def test_an_overlong_username_is_a_form_error_not_a_500(self, _):
        response = self.client.post(SIGNUP_URL, signup_payload(username='x' * 33))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "za długa")
        self.assertEqual(User.objects.count(), self.accounts_before)

    @TURNSTILE_OK
    def test_an_underage_birth_date_is_refused(self, _):
        from django.utils import timezone

        recent = timezone.localdate().replace(year=timezone.localdate().year - 10)
        response = self.client.post(
            SIGNUP_URL, signup_payload(date_of_birth=recent.isoformat()),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Musisz mieć przynajmniej")
        self.assertEqual(User.objects.count(), self.accounts_before)

    @TURNSTILE_OK
    def test_the_password_house_rules_still_hold(self, _):
        response = self.client.post(
            SIGNUP_URL, signup_payload(password1='alllowercase', password2='alllowercase'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), self.accounts_before)

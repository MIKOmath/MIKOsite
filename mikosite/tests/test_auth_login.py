"""Login: by username or email, uniform errors, verified members only."""
from django.core.cache import cache
from django.test import TestCase

from accounts.models import User

from .auth_base import PASSWORD, make_verified_user

LOGIN_URL = '/accounts/login/'


class LoginPageTests(TestCase):
    def test_the_page_wears_the_house_shell(self):
        response = self.client.get(LOGIN_URL)

        self.assertEqual(response.status_code, 200)
        for marker in ('auth-card', 'Logowanie', 'Nie pamiętasz hasła?', 'Zarejestruj się'):
            self.assertContains(response, marker)

    def test_no_social_buttons_render_without_configured_providers(self):
        # Forced empty rather than inherited: the developer machine may well
        # have real OAuth keys in secrets.py, and this test is about the
        # unconfigured state, not about this machine.
        with self.settings(SOCIALACCOUNT_PROVIDERS={}):
            response = self.client.get(LOGIN_URL)

        self.assertNotContains(response, 'Kontynuuj przez')

    def test_the_old_address_still_arrives_here(self):
        response = self.client.get('/signin/')

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers['Location'], LOGIN_URL)

    def test_the_header_links_to_the_new_login(self):
        response = self.client.get('/')

        self.assertContains(response, f'href="{LOGIN_URL}"')


class LoginFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_verified_user()

    def test_login_by_username(self):
        response = self.client.post(LOGIN_URL, {'login': 'marek123', 'password': PASSWORD})

        self.assertEqual(response.headers['Location'], '/')

    def test_login_by_email(self):
        response = self.client.post(LOGIN_URL, {'login': 'marek@test.com', 'password': PASSWORD})

        self.assertEqual(response.headers['Location'], '/')

    def test_wrong_credentials_get_one_uniform_answer(self):
        bad_password = self.client.post(LOGIN_URL, {'login': 'marek123', 'password': 'Wrong1!pass'})
        no_such_user = self.client.post(LOGIN_URL, {'login': 'nikttaki', 'password': 'Wrong1!pass'})

        self.assertEqual(bad_password.status_code, 200)
        self.assertEqual(no_such_user.status_code, 200)
        self.assertEqual(
            bad_password.context['form'].errors, no_such_user.context['form'].errors,
        )

    def test_an_unverified_member_is_sent_to_verification_not_in(self):
        User.objects.create_user(username='nowy', email='nowy@test.com', password=PASSWORD)

        response = self.client.post(LOGIN_URL, {'login': 'nowy', 'password': PASSWORD})

        self.assertEqual(response.status_code, 302)
        self.assertIn('confirm-email', response.headers['Location'])

    def test_signout_still_works_from_its_old_address(self):
        self.client.post(LOGIN_URL, {'login': 'marek123', 'password': PASSWORD})

        response = self.client.get('/signout/')

        self.assertEqual(response.headers['Location'], '/')
        self.assertNotIn('_auth_user_id', self.client.session)


class StandalonePageTests(TestCase):
    """Pages no flow test reaches; a template error here would otherwise hide."""

    def test_the_standalone_pages_wear_the_house_shell(self):
        pages = {
            '/accounts/inactive/': 200,
            '/accounts/password/reset/done/': 200,
            '/accounts/3rdparty/login/error/': 401,
            '/accounts/3rdparty/login/cancelled/': 200,
        }
        for url, status in pages.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, 'auth-card', status_code=status)

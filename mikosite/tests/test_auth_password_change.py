"""Password change: the allauth flow, which keeps the session alive."""
from django.core.cache import cache
from django.test import TestCase

from accounts.models import User
from allauth.account.models import EmailAddress

from .auth_base import NEW_PASSWORD, PASSWORD, make_verified_user

CHANGE_URL = '/accounts/password/change/'
LOGIN_URL = '/accounts/login/'


class PasswordChangeTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_verified_user()
        self.client.post(LOGIN_URL, {'login': 'marek123', 'password': PASSWORD})

    def change(self, old, new):
        return self.client.post(
            CHANGE_URL, {'oldpassword': old, 'password1': new, 'password2': new},
        )

    def test_anonymous_callers_are_sent_to_login(self):
        self.client.get('/signout/')

        response = self.client.get(CHANGE_URL)

        self.assertEqual(response.status_code, 302)
        self.assertIn(LOGIN_URL, response.headers['Location'])

    def test_the_page_wears_the_house_shell(self):
        response = self.client.get(CHANGE_URL)

        self.assertEqual(response.status_code, 200)
        for marker in ('auth-card', 'Zmiana hasła', 'password-rules'):
            self.assertContains(response, marker)

    def test_the_old_address_still_arrives_here(self):
        response = self.client.get('/change_password/')

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers['Location'], CHANGE_URL)

    def test_changing_the_password_does_not_log_the_member_out(self):
        """The retired view forgot update_session_auth_hash, so a successful
        change ended the session. The allauth flow must not regress that."""
        self.change(PASSWORD, NEW_PASSWORD)

        response = self.client.get('/profile/')

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))

    def test_a_wrong_old_password_changes_nothing(self):
        response = self.change('Wrong1!pass', NEW_PASSWORD)

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_the_house_password_rules_apply(self):
        response = self.change(PASSWORD, 'alllowercase')

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_success_lands_on_the_profile(self):
        response = self.change(PASSWORD, NEW_PASSWORD)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/profile/')

    def test_the_profile_offers_a_change_button_to_a_password_user(self):
        response = self.client.get('/profile/')

        self.assertContains(response, 'Zmień hasło')
        self.assertContains(response, '/accounts/password/change/')
        self.assertNotContains(response, 'Ustaw hasło')


class PasswordSetTests(TestCase):
    """A social-only member setting their first password."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='spoleczny', email='spoleczny@test.com', password=PASSWORD,
        )
        self.user.set_unusable_password()
        self.user.save()
        EmailAddress.objects.create(
            user=self.user, email='spoleczny@test.com', verified=True, primary=True,
        )
        self.client.force_login(self.user)

    def test_the_profile_offers_a_set_button_to_a_passwordless_user(self):
        response = self.client.get('/profile/')

        self.assertContains(response, 'Ustaw hasło')
        self.assertContains(response, '/accounts/password/set/')
        self.assertNotContains(response, 'Zmień hasło')

    def test_the_change_url_hands_a_passwordless_user_to_the_set_page(self):
        response = self.client.get(CHANGE_URL)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/accounts/password/set/')

    def test_setting_the_first_password_lands_on_the_profile(self):
        response = self.client.post(
            '/accounts/password/set/', {'password1': NEW_PASSWORD, 'password2': NEW_PASSWORD},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/profile/')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))

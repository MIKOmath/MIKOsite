"""Social linkage: one account per provider, admin surfaces, provider buttons."""
from django.test import RequestFactory, TestCase, override_settings

from accounts.adapters import SocialAccountAdapter
from accounts.models import User
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialAccount, SocialLogin

PASSWORD = 'Correct1!horse'


def make_user(username, email=None):
    return User.objects.create_user(
        username=username, email=email or f'{username}@test.com', password=PASSWORD,
    )



class OnePerProviderTests(TestCase):
    def setUp(self):
        self.member = make_user('marek123')
        self.factory = RequestFactory()
        self.adapter = SocialAccountAdapter()

    def connect_attempt(self, provider='discord', uid='222'):
        sociallogin = SocialLogin(account=SocialAccount(provider=provider, uid=uid))
        sociallogin.state = {'process': 'connect'}
        request = self.factory.get('/accounts/discord/login/callback/')
        request.user = self.member
        return sociallogin, request

    def test_a_second_account_of_the_same_provider_is_refused(self):
        SocialAccount.objects.create(user=self.member, provider='discord', uid='111')
        sociallogin, request = self.connect_attempt()

        with self.assertRaises(ImmediateHttpResponse) as caught:
            self.adapter.pre_social_login(request, sociallogin)

        self.assertIn('juz-polaczone', caught.exception.response.headers['Location'])

    def test_the_first_account_of_a_provider_connects_freely(self):
        sociallogin, request = self.connect_attempt()

        self.adapter.pre_social_login(request, sociallogin)  # must not raise

    def test_a_different_provider_connects_freely(self):
        SocialAccount.objects.create(user=self.member, provider='discord', uid='111')
        sociallogin, request = self.connect_attempt(provider='google')

        self.adapter.pre_social_login(request, sociallogin)  # must not raise


class PopulateUserTests(TestCase):
    """What provider data lands on the fresh user before the completion form."""

    def populate(self, provider, data):
        adapter = SocialAccountAdapter()
        sociallogin = SocialLogin(
            user=User(), account=SocialAccount(provider=provider, uid='1'),
        )
        return adapter.populate_user(None, sociallogin, data)

    def test_a_discord_username_is_not_poured_into_the_name_fields(self):
        user = self.populate('discord', {'username': 'xX_gamer_Xx', 'name': 'xX_gamer_Xx'})

        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')

    def test_googles_real_name_fields_still_arrive(self):
        user = self.populate('google', {'first_name': 'Ewa', 'last_name': 'Testowa'})

        self.assertEqual(user.first_name, 'Ewa')
        self.assertEqual(user.last_name, 'Testowa')


DEMO_PROVIDERS = {
    'google': {'APPS': [{'client_id': 'demo-id', 'secret': 'demo-secret'}]},
    'discord': {'APPS': [{'client_id': 'demo-id', 'secret': 'demo-secret'}]},
}


@override_settings(SOCIALACCOUNT_PROVIDERS=DEMO_PROVIDERS)
class ProviderButtonTests(TestCase):
    """Configured providers surface everywhere on their own; unconfigured ones
    stay invisible (the inverse is pinned in test_auth_login)."""

    def test_the_login_page_offers_the_providers(self):
        response = self.client.get('/accounts/login/')

        self.assertContains(response, 'Kontynuuj przez Google')
        self.assertContains(response, 'Kontynuuj przez Discord')
        self.assertContains(response, 'process=login')

    def test_the_connections_page_offers_to_link_them(self):
        from allauth.account.models import EmailAddress

        member = make_user('marek123')
        EmailAddress.objects.create(
            user=member, email=member.email, verified=True, primary=True,
        )
        self.client.post(
            '/accounts/login/', {'login': 'marek123', 'password': PASSWORD},
        )

        response = self.client.get('/accounts/3rdparty/')

        self.assertContains(response, 'Połącz nowe konto')
        self.assertContains(response, 'process=connect')

    def test_the_button_leaves_for_the_provider_without_an_interstitial(self):
        """SOCIALACCOUNT_LOGIN_ON_GET: one click, straight to the provider -
        no "Continue" confirmation page in between."""
        response = self.client.get('/accounts/google/login/?process=login')

        self.assertEqual(response.status_code, 302)
        self.assertIn('accounts.google.com', response.headers['Location'])


@override_settings(SOCIALACCOUNT_PROVIDERS=DEMO_PROVIDERS)
class ConnectionsPageTests(TestCase):
    """The connections page guides a passwordless member to set a password,
    because every change there is reauthentication-gated. Providers are forced
    so rendering provider data never depends on the developer's OAuth keys."""

    def login_as(self, user):
        self.client.force_login(user)

    def test_a_passwordless_member_is_pointed_at_setting_a_password(self):
        member = make_user('spoleczny')
        member.set_unusable_password()
        member.save()
        self.login_as(member)

        response = self.client.get('/accounts/3rdparty/')

        self.assertContains(response, 'Najpierw ustaw hasło')

    def test_a_member_with_a_password_sees_no_such_hint(self):
        self.login_as(make_user('zwykly'))

        response = self.client.get('/accounts/3rdparty/')

        self.assertNotContains(response, 'Najpierw ustaw hasło')

    def test_each_connected_account_gets_its_own_tile_and_disconnect_form(self):
        member = make_user('kafelki')
        account = SocialAccount.objects.create(user=member, provider='discord', uid='777')
        self.login_as(member)

        response = self.client.get('/accounts/3rdparty/')

        self.assertContains(response, 'auth-connection')
        self.assertContains(response, f'name="account" value="{account.pk}"')
        self.assertContains(response, 'Odłącz')
        self.assertContains(response, 'disconnect-dialog')
        self.assertNotContains(response, 'type="radio"')

    def test_the_disconnect_post_still_works_without_the_dialog(self):
        """The dialog is client-side sugar; the plain POST is the contract."""
        member = make_user('odlaczam')
        SocialAccount.objects.create(user=member, provider='discord', uid='888')
        SocialAccount.objects.create(user=member, provider='google', uid='999')
        google = SocialAccount.objects.get(provider='google')
        self.login_as(member)

        with self.settings(ACCOUNT_REAUTHENTICATION_REQUIRED=False):
            self.client.post('/accounts/3rdparty/', {'account': google.pk})

        self.assertFalse(SocialAccount.objects.filter(pk=google.pk).exists())


class SocialAdminTests(TestCase):
    def test_only_the_account_linkage_is_in_the_admin(self):
        from django.contrib import admin
        from allauth.socialaccount.models import SocialApp, SocialToken

        self.assertIn(SocialAccount, admin.site._registry)
        for model in (SocialApp, SocialToken):
            self.assertNotIn(model, admin.site._registry)

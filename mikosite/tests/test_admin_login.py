"""The admin panel sends people to the site's login page, not its own."""
from allauth.account.models import EmailAddress
from django.test import TestCase

from accounts.models import User

PASSWORD = 'Testpass1!'
SITE_LOGIN = '/accounts/login/'


class AdminLoginRedirectTests(TestCase):
    def test_an_anonymous_visitor_lands_on_the_site_login(self):
        response = self.client.get('/admin/', follow=True)

        self.assertEqual(response.redirect_chain[-1][0], f'{SITE_LOGIN}?next=/admin/')
        self.assertEqual(response.status_code, 200)

    def test_the_page_they_were_after_is_carried_through(self):
        response = self.client.get('/admin/seminars/seminar/', follow=True)

        self.assertEqual(response.redirect_chain[-1][0],
                         f'{SITE_LOGIN}?next=/admin/seminars/seminar/')

    def test_the_panels_own_form_is_no_longer_served(self):
        response = self.client.get('/admin/login/')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith(SITE_LOGIN))

    def test_an_off_site_destination_is_dropped(self):
        response = self.client.get('/admin/login/?next=https://evil.invalid/steal')

        self.assertEqual(response['Location'], f'{SITE_LOGIN}?next=/admin/')

    def test_signing_in_from_there_comes_back_to_the_panel(self):
        boss = User.objects.create_superuser(
            username='boss', email='boss@test.com', password=PASSWORD,
        )
        EmailAddress.objects.create(user=boss, email=boss.email, verified=True, primary=True)
        landed = self.client.get('/admin/', follow=True).redirect_chain[-1][0]

        response = self.client.post(landed, {'login': 'boss', 'password': PASSWORD})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/admin/')


class AdminLoginSignedInTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = User.objects.create_user(
            username='member', email='member@test.com', password=PASSWORD,
        )
        cls.boss = User.objects.create_superuser(
            username='boss', email='boss@test.com', password=PASSWORD,
        )

    def test_an_account_without_staff_rights_gets_the_house_page(self):
        self.client.force_login(self.member)

        response = self.client.get('/admin/login/')

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, 'admin_no_access.html')
        self.assertContains(response, "Brak dostępu do panelu", status_code=403)

    def test_the_house_page_names_the_account_they_are_signed_in_as(self):
        self.client.force_login(self.member)

        response = self.client.get('/admin/login/')

        self.assertContains(response, 'member', status_code=403)

    def test_the_panels_own_form_is_never_what_they_see(self):
        self.client.force_login(self.member)

        response = self.client.get('/admin/', follow=True)

        self.assertTemplateNotUsed(response, 'admin/login.html')
        self.assertEqual(response.status_code, 403)

    def test_an_account_deactivated_mid_session_counts_as_signed_out(self):
        """Django resolves an inactive session back to anonymous, so these see
        the login page rather than the one explaining they lack rights."""
        self.client.force_login(self.member)
        User.objects.filter(pk=self.member.pk).update(is_active=False)

        response = self.client.get('/admin/login/')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith(SITE_LOGIN))

    def test_an_administrator_goes_straight_to_the_panel(self):
        self.client.force_login(self.boss)

        response = self.client.get('/admin/login/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/admin/')

    def test_staff_without_superuser_rights_still_reach_the_panel(self):
        staffer = User.objects.create_user(
            username='staffer', email='staffer@test.com', password=PASSWORD, is_staff=True,
        )
        self.client.force_login(staffer)

        response = self.client.get('/admin/login/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/admin/')

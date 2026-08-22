"""Partners and registration events, and the switch that hides either one."""
import tempfile
from datetime import date, timedelta

from django.test import override_settings
from django.utils import timezone
from rest_framework import status

from mainSite.models import Partner, RegistrationEvent

from .api_base import ApiPlaneTestCase, tiny_image

PUBLIC_PARTNER_FIELDS = {'id', 'name', 'logo', 'url', 'badge', 'is_featured'}
ADMIN_PARTNER_FIELDS = PUBLIC_PARTNER_FIELDS | {'order', 'is_published'}

PUBLIC_EVENT_FIELDS = {
    'id', 'kind', 'name', 'title', 'location', 'date_begin', 'date_end', 'date_range',
    'registration_begin', 'registration_end', 'registration_range', 'registration_url',
    'registration_open', 'image_url',
}
ADMIN_EVENT_FIELDS = {
    'id', 'name', 'location', 'date_begin', 'date_end', 'registration_begin',
    'registration_end', 'registration_url', 'image', 'is_published',
}


def make_event(name, **kwargs):
    defaults = {
        'location': "Warszawa",
        'date_begin': date(2026, 3, 5),
        'date_end': date(2026, 3, 7),
        'registration_begin': date(2026, 2, 1),
        'registration_end': date(2026, 3, 1),
        'registration_url': 'https://example.invalid/',
    }
    return RegistrationEvent.objects.create(name=name, **{**defaults, **kwargs})


class PartnerReadTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.shown = Partner.objects.create(name="Widoczny", url='https://example.invalid/', order=1)
        cls.hidden = Partner.objects.create(name="Ukryty", is_published=False, order=2)

    def test_anyone_may_read_the_partners(self):
        response = self.client.get('/api/partners/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data['results'][0]), PUBLIC_PARTNER_FIELDS)

    def test_an_unpublished_partner_is_invisible_off_the_administrator_plane(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                names = [item['name'] for item in self.client.get('/api/partners/').data['results']]
                self.assertEqual(names, ["Widoczny"])

    def test_an_unpublished_partner_is_not_reachable_by_id_either(self):
        self.as_member()

        response = self.client.get(f'/api/partners/{self.hidden.pk}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_an_administrator_sees_both_and_the_switch(self):
        self.as_admin()

        response = self.client.get('/api/partners/')

        self.assertEqual(response.data['count'], 2)
        self.assertEqual(set(response.data['results'][0]), ADMIN_PARTNER_FIELDS)

    def test_partners_come_back_in_their_display_order(self):
        Partner.objects.create(name="Pierwszy", order=0)

        names = [item['name'] for item in self.client.get('/api/partners/').data['results']]

        self.assertEqual(names, ["Pierwszy", "Widoczny"])


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PartnerWriteTests(ApiPlaneTestCase):
    def test_writing_is_refused_off_the_administrator_plane(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                response = self.client.post(
                    '/api/partners/', {'name': "Nowy", 'logo': tiny_image()},
                )
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_an_administrator_may_add_and_then_hide_a_partner(self):
        self.as_admin()

        created = self.client.post('/api/partners/', {'name': "Nowy", 'logo': tiny_image()})
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        hidden = self.client.patch(f"/api/partners/{created.data['id']}/", {'is_published': False})
        self.assertEqual(hidden.status_code, status.HTTP_200_OK)

        self.as_anonymous()
        self.assertEqual(self.client.get('/api/partners/').data['count'], 0)


class RegistrationEventReadTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.shown = make_event("Zjazd MIKO")
        cls.hidden = make_event("Zjazd ukryty", is_published=False)

    def test_anyone_may_read_the_events(self):
        response = self.client.get('/api/registration-events/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data['results'][0]), PUBLIC_EVENT_FIELDS)

    def test_an_unpublished_event_is_invisible_off_the_administrator_plane(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                names = [
                    item['name']
                    for item in self.client.get('/api/registration-events/').data['results']
                ]
                self.assertEqual(names, ["Zjazd MIKO"])

    def test_an_administrator_sees_both_and_the_switch(self):
        self.as_admin()

        response = self.client.get('/api/registration-events/')

        self.assertEqual(response.data['count'], 2)
        self.assertEqual(set(response.data['results'][0]), ADMIN_EVENT_FIELDS)

    def test_the_public_shape_carries_the_labels_the_calendar_draws(self):
        response = self.client.get(f'/api/registration-events/{self.shown.pk}/')

        self.assertEqual(response.data['kind'], 'registration_event')
        self.assertEqual(response.data['title'], "Zjazd MIKO")
        self.assertEqual(response.data['date_range'], "5-7 marca")
        self.assertEqual(response.data['registration_range'], "1 lutego - 1 marca")

    def test_an_event_without_a_photograph_falls_back_to_the_default(self):
        response = self.client.get(f'/api/registration-events/{self.shown.pk}/')

        self.assertIn('MIKO_GATHERING', response.data['image_url'])

    def test_the_open_flag_is_judged_against_today(self):
        today = timezone.localdate()
        open_now = make_event(
            "Otwarte",
            registration_begin=today - timedelta(days=1),
            registration_end=today + timedelta(days=1),
        )

        response = self.client.get(f'/api/registration-events/{open_now.pk}/')

        self.assertTrue(response.data['registration_open'])
        self.assertFalse(
            self.client.get(f'/api/registration-events/{self.shown.pk}/').data['registration_open'],
        )

    def test_the_date_window_filters_both_ends(self):
        make_event("Późny", date_begin=date(2026, 6, 1), date_end=date(2026, 6, 3))

        names = [
            item['name']
            for item in self.client.get(
                '/api/registration-events/', {'start_date': '2026-05-01'},
            ).data['results']
        ]

        self.assertEqual(names, ["Późny"])


class RegistrationEventWriteTests(ApiPlaneTestCase):
    payload = {
        'name': "Nowy zjazd",
        'location': "Kraków",
        'date_begin': '2026-07-01',
        'date_end': '2026-07-03',
        'registration_begin': '2026-05-01',
        'registration_end': '2026-06-01',
        'registration_url': 'https://example.invalid/',
    }

    def test_writing_is_refused_off_the_administrator_plane(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                self.assertEqual(
                    self.client.post('/api/registration-events/', self.payload).status_code,
                    status.HTTP_403_FORBIDDEN,
                )

    def test_an_administrator_may_create_an_event(self):
        self.as_admin()

        response = self.client.post('/api/registration-events/', self.payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_an_event_ending_before_it_begins_is_refused(self):
        self.as_admin()

        response = self.client.post(
            '/api/registration-events/', {**self.payload, 'date_end': '2026-06-30'},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date_end', response.data)

    def test_a_registration_window_that_closes_before_it_opens_is_refused(self):
        self.as_admin()

        response = self.client.post(
            '/api/registration-events/', {**self.payload, 'registration_end': '2026-04-01'},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('registration_end', response.data)

    def test_the_rule_still_holds_when_only_one_date_is_patched(self):
        self.as_admin()
        created = self.client.post('/api/registration-events/', self.payload)

        response = self.client.patch(
            f"/api/registration-events/{created.data['id']}/", {'date_end': '2026-06-01'},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

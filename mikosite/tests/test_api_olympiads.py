"""Olympiads and their stages, newly reachable through the API."""
from datetime import date

from rest_framework import status

from olympiads.models import Olympiad, OlympiadStage

from .api_base import ApiPlaneTestCase

PUBLIC_OLYMPIAD_FIELDS = {'id', 'name', 'short_name', 'logo', 'website_url'}
ADMIN_OLYMPIAD_FIELDS = PUBLIC_OLYMPIAD_FIELDS | {'order', 'is_active'}

PUBLIC_STAGE_FIELDS = {
    'id', 'kind', 'stage_label', 'title', 'date_begin', 'date_end', 'date_range',
    'location', 'url', 'note', 'olympiad',
}
ADMIN_STAGE_FIELDS = {
    'id', 'olympiad', 'name', 'date_begin', 'date_end', 'location', 'url', 'note', 'is_published',
}


class OlympiadReadTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.active = Olympiad.objects.get(short_name="OM")
        cls.inactive = Olympiad.objects.create(
            name="Olimpiada Ukryta", short_name="OU", is_active=False,
        )

    def test_anyone_may_read_the_olympiads(self):
        response = self.client.get('/api/olympiads/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data['results'][0]), PUBLIC_OLYMPIAD_FIELDS)

    def test_an_inactive_olympiad_is_invisible_off_the_administrator_plane(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                names = [item['short_name'] for item in self.client.get('/api/olympiads/').data['results']]
                self.assertNotIn("OU", names)

    def test_an_inactive_olympiad_is_not_reachable_by_id_either(self):
        response = self.client.get(f'/api/olympiads/{self.inactive.pk}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_an_administrator_sees_the_inactive_one_and_the_switch(self):
        self.as_admin()

        response = self.client.get(f'/api/olympiads/{self.inactive.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), ADMIN_OLYMPIAD_FIELDS)

    def test_the_seeded_order_is_preserved(self):
        names = [item['short_name'] for item in self.client.get('/api/olympiads/').data['results']]

        self.assertEqual(names, ["OM", "OI", "AI"])


class OlympiadStageReadTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.olympiad = Olympiad.objects.get(short_name="OM")
        cls.olympiad.website_url = 'https://example.invalid/om/'
        cls.olympiad.save()
        cls.shown = OlympiadStage.objects.create(
            olympiad=cls.olympiad, name="II etap",
            date_begin=date(2026, 3, 10), date_end=date(2026, 3, 11), location="cała Polska",
        )
        cls.hidden = OlympiadStage.objects.create(
            olympiad=cls.olympiad, name="Etap ukryty",
            date_begin=date(2026, 4, 10), date_end=date(2026, 4, 11), is_published=False,
        )

    def test_anyone_may_read_the_stages(self):
        response = self.client.get('/api/olympiad-stages/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data['results'][0]), PUBLIC_STAGE_FIELDS)

    def test_the_public_shape_carries_the_labels_the_calendar_draws(self):
        response = self.client.get(f'/api/olympiad-stages/{self.shown.pk}/')

        self.assertEqual(response.data['kind'], 'olympiad')
        self.assertEqual(response.data['title'], "OM – II etap")
        self.assertEqual(response.data['stage_label'], "II etap")
        self.assertEqual(response.data['date_range'], "10-11 marca")

    def test_a_stage_without_a_link_borrows_the_olympiads(self):
        response = self.client.get(f'/api/olympiad-stages/{self.shown.pk}/')

        self.assertEqual(response.data['url'], 'https://example.invalid/om/')

    def test_the_nested_olympiad_is_the_public_shape(self):
        response = self.client.get(f'/api/olympiad-stages/{self.shown.pk}/')

        self.assertEqual(set(response.data['olympiad']), PUBLIC_OLYMPIAD_FIELDS)

    def test_an_unpublished_stage_is_invisible_off_the_administrator_plane(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                labels = [
                    item['stage_label']
                    for item in self.client.get('/api/olympiad-stages/').data['results']
                ]
                self.assertEqual(labels, ["II etap"])

    def test_switching_off_the_olympiad_takes_its_stages_with_it(self):
        self.olympiad.is_active = False
        self.olympiad.save()

        self.assertEqual(self.client.get('/api/olympiad-stages/').data['count'], 0)

    def test_an_administrator_sees_the_hidden_stage_and_the_switch(self):
        self.as_admin()

        response = self.client.get(f'/api/olympiad-stages/{self.hidden.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), ADMIN_STAGE_FIELDS)

    def test_stages_may_be_narrowed_to_one_olympiad_and_a_date_window(self):
        other = Olympiad.objects.get(short_name="OI")
        OlympiadStage.objects.create(
            olympiad=other, name="II etap",
            date_begin=date(2026, 5, 10), date_end=date(2026, 5, 11),
        )

        by_olympiad = self.client.get('/api/olympiad-stages/', {'olympiad': other.pk})
        by_window = self.client.get('/api/olympiad-stages/', {'start_date': '2026-05-01'})

        self.assertEqual(by_olympiad.data['count'], 1)
        self.assertEqual(by_window.data['count'], 1)

    def test_the_olympiad_is_joined_rather_than_fetched_per_row(self):
        for day in range(1, 11):
            OlympiadStage.objects.create(
                olympiad=self.olympiad, name=f"Etap {day}",
                date_begin=date(2026, 6, day), date_end=date(2026, 6, day),
            )

        with self.assertNumQueries(2):  # count, then the page with its join
            self.client.get('/api/olympiad-stages/')


class OlympiadWriteTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.olympiad = Olympiad.objects.get(short_name="OM")

    def stage_payload(self):
        return {
            'olympiad': self.olympiad.pk,
            'name': "Finał",
            'date_begin': '2026-04-08',
            'date_end': '2026-04-10',
        }

    def test_writing_is_refused_off_the_administrator_plane(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                self.assertEqual(
                    self.client.post('/api/olympiads/', {'name': "Nowa", 'short_name': "N"}).status_code,
                    status.HTTP_403_FORBIDDEN,
                )
                self.assertEqual(
                    self.client.post('/api/olympiad-stages/', self.stage_payload()).status_code,
                    status.HTTP_403_FORBIDDEN,
                )

    def test_an_administrator_may_create_a_stage(self):
        self.as_admin()

        response = self.client.post('/api/olympiad-stages/', self.stage_payload())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_a_stage_ending_before_it_begins_is_refused(self):
        self.as_admin()

        response = self.client.post(
            '/api/olympiad-stages/', {**self.stage_payload(), 'date_end': '2026-04-07'},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date_end', response.data)

    def test_a_stage_overlapping_the_same_stage_is_refused(self):
        self.as_admin()
        self.client.post('/api/olympiad-stages/', self.stage_payload())

        response = self.client.post(
            '/api/olympiad-stages/',
            {**self.stage_payload(), 'date_begin': '2026-04-09', 'date_end': '2026-04-12'},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date_begin', response.data)

    def test_editing_a_stage_does_not_count_it_as_overlapping_itself(self):
        self.as_admin()
        created = self.client.post('/api/olympiad-stages/', self.stage_payload())

        response = self.client.patch(
            f"/api/olympiad-stages/{created.data['id']}/", {'location': "Warszawa"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

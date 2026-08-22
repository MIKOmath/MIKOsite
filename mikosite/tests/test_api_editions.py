"""Previous editions: a short public shape, the full record for administrators."""
from datetime import date, time, timedelta

from rest_framework import status

from seminars.models import PreviousEdition, PreviousEditionMilestone, Seminar

from .api_base import ApiPlaneTestCase

PUBLIC_FIELDS = {
    'id', 'school_year_label', 'start_date', 'end_date', 'member_count_label', 'brochure_url',
}
ADMIN_FIELDS = {
    'id', 'school_year_label', 'start_date', 'end_date', 'member_count',
    'member_count_is_estimate', 'brochure', 'is_published', 'seminar_count', 'milestones',
}
# The public plane gets the rounded label, never the working figures, the
# timeline, or the publication switch.
ADMIN_ONLY_FIELDS = ADMIN_FIELDS - PUBLIC_FIELDS


class PreviousEditionReadTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.edition = PreviousEdition.objects.create(
            start_date=date(2024, 9, 1), end_date=date(2025, 6, 20),
            member_count=2000, member_count_is_estimate=True,
        )
        PreviousEditionMilestone.objects.create(
            edition=cls.edition, date=date(2024, 10, 1), title="Start",
        )
        cls.hidden = PreviousEdition.objects.create(
            start_date=date(2023, 9, 1), end_date=date(2024, 6, 20), is_published=False,
        )

    def test_anyone_may_read_the_editions(self):
        response = self.client.get('/api/previous-editions/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data['results'][0]), PUBLIC_FIELDS)

    def test_the_public_shape_is_the_basic_record_and_the_brochure_link(self):
        response = self.client.get(f'/api/previous-editions/{self.edition.pk}/')

        self.assertEqual(response.data['school_year_label'], "Rok szkolny 2024/25")
        self.assertEqual(response.data['member_count_label'], "2000+")
        self.assertIn('brochure_url', response.data)

    def test_the_public_shape_withholds_the_working_record(self):
        response = self.client.get(f'/api/previous-editions/{self.edition.pk}/')

        self.assertEqual(set(response.data) & ADMIN_ONLY_FIELDS, set())

    def test_an_edition_with_no_brochure_reports_no_link(self):
        response = self.client.get(f'/api/previous-editions/{self.edition.pk}/')

        self.assertIsNone(response.data['brochure_url'])

    def test_an_unpublished_edition_is_invisible_off_the_administrator_plane(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                response = self.client.get('/api/previous-editions/')
                self.assertEqual(response.data['count'], 1)
                self.assertEqual(
                    self.client.get(f'/api/previous-editions/{self.hidden.pk}/').status_code,
                    status.HTTP_404_NOT_FOUND,
                )

    def test_an_administrator_sees_the_full_record(self):
        self.as_admin()

        response = self.client.get(f'/api/previous-editions/{self.edition.pk}/')

        self.assertEqual(set(response.data), ADMIN_FIELDS)
        self.assertEqual(response.data['member_count'], 2000)
        self.assertEqual(response.data['milestones'][0]['title'], "Start")

    def test_the_administrator_shape_counts_the_seminars_of_the_edition(self):
        Seminar.objects.create(
            date=date(2024, 10, 5), time=time(18, 0), duration=timedelta(hours=1), theme="W środku",
        )
        Seminar.objects.create(
            date=date(2026, 10, 5), time=time(18, 0), duration=timedelta(hours=1), theme="Poza",
        )
        self.as_admin()

        response = self.client.get(f'/api/previous-editions/{self.edition.pk}/')

        self.assertEqual(response.data['seminar_count'], 1)

    def test_an_edition_with_no_seminars_counts_zero_rather_than_null(self):
        self.as_admin()

        response = self.client.get(f'/api/previous-editions/{self.edition.pk}/')

        self.assertEqual(response.data['seminar_count'], 0)

    def test_counting_seminars_does_not_cost_a_query_per_edition(self):
        for year in range(2015, 2023):
            PreviousEdition.objects.create(
                start_date=date(year, 9, 1), end_date=date(year + 1, 6, 20),
            )
        self.as_admin()

        with self.assertNumQueries(3):  # count, page with the subquery, prefetched milestones
            self.client.get('/api/previous-editions/')

    def test_the_public_plane_pays_for_neither_the_timeline_nor_the_tally(self):
        with self.assertNumQueries(2):  # count, then the page
            self.client.get('/api/previous-editions/')


class PreviousEditionWriteTests(ApiPlaneTestCase):
    payload = {'start_date': '2024-09-01', 'end_date': '2025-06-20'}

    def test_writing_is_refused_off_the_administrator_plane(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                self.assertEqual(
                    self.client.post('/api/previous-editions/', self.payload).status_code,
                    status.HTTP_403_FORBIDDEN,
                )

    def test_an_administrator_may_create_an_edition(self):
        self.as_admin()

        response = self.client.post('/api/previous-editions/', self.payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_an_edition_ending_before_it_begins_is_refused(self):
        self.as_admin()

        response = self.client.post(
            '/api/previous-editions/', {**self.payload, 'end_date': '2024-08-01'},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_date', response.data)

    def test_an_edition_overlapping_another_is_refused(self):
        self.as_admin()
        self.client.post('/api/previous-editions/', self.payload)

        response = self.client.post(
            '/api/previous-editions/', {'start_date': '2025-01-01', 'end_date': '2025-12-31'},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_date', response.data)

    def test_editing_an_edition_does_not_count_it_as_overlapping_itself(self):
        self.as_admin()
        created = self.client.post('/api/previous-editions/', self.payload)

        response = self.client.patch(
            f"/api/previous-editions/{created.data['id']}/", {'member_count': 1500},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

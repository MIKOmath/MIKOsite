"""The two places the weekly sheet can be picked up: /kolo/ and the admin panel."""
from datetime import date, timedelta

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from seminars.timetable_image import (
    featured_week_downloads,
    offered_week_downloads,
    offered_week_starts,
    week_start_of,
)

ADMIN_PAGE = '/admin/seminars/seminar/plan-tygodnia/'
PASSWORD = 'Testpass1!'


class OfferedWeekDownloadTests(TestCase):
    def test_every_week_on_offer_is_listed_once(self):
        downloads = offered_week_downloads()

        self.assertEqual([week['week_start'] for week in downloads], offered_week_starts())

    def test_each_link_points_at_its_own_week(self):
        for week in offered_week_downloads():
            with self.subTest(week=week['week_start']):
                self.assertIn(f"week={week['week_start'].isoformat()}", week['url'])
                self.assertIn(week['week_start'].isoformat(), week['filename'])


class FeaturedWeekTests(TestCase):
    """The page offers this week and the next, and marks the useful one."""

    MONDAY = date(2026, 3, 2)

    def featured_on(self, day_offset):
        return featured_week_downloads(self.MONDAY + timedelta(days=day_offset))

    def test_only_this_week_and_the_next_are_offered(self):
        starts = [week['week_start'] for week in self.featured_on(0)]

        self.assertEqual(starts, [self.MONDAY, self.MONDAY + timedelta(weeks=1)])

    def test_early_in_the_week_the_week_we_are_in_is_suggested(self):
        for day_offset, name in enumerate(('poniedziałek', 'wtorek', 'środa')):
            with self.subTest(day=name):
                suggested = [week['week_start'] for week in self.featured_on(day_offset)
                             if week['is_suggested']]

                self.assertEqual(suggested, [self.MONDAY])

    def test_from_thursday_the_next_week_is_suggested(self):
        for day_offset, name in enumerate(('czwartek', 'piątek', 'sobota', 'niedziela'), start=3):
            with self.subTest(day=name):
                suggested = [week['week_start'] for week in self.featured_on(day_offset)
                             if week['is_suggested']]

                self.assertEqual(suggested, [self.MONDAY + timedelta(weeks=1)])

    def test_exactly_one_week_is_ever_suggested(self):
        for day_offset in range(7):
            with self.subTest(day_offset=day_offset):
                featured = self.featured_on(day_offset)

                self.assertEqual(sum(week['is_suggested'] for week in featured), 1)


class KoloPageDownloadTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_the_page_offers_this_week_and_the_next(self):
        response = self.client.get('/kolo/')
        this_week = week_start_of(timezone.localdate())

        self.assertEqual(response.status_code, 200)
        for monday in (this_week, this_week + timedelta(weeks=1)):
            self.assertContains(response, f"/api/calendar/image/?week={monday.isoformat()}")

    def test_the_links_ask_the_browser_to_save_the_file(self):
        response = self.client.get('/kolo/')

        self.assertContains(response, 'download="miko-plan-')

    def test_the_page_leaves_out_the_weeks_it_does_not_feature(self):
        response = self.client.get('/kolo/')
        this_week = week_start_of(timezone.localdate())

        for monday in (this_week - timedelta(weeks=1), this_week + timedelta(weeks=2)):
            self.assertNotContains(response, f"week={monday.isoformat()}")

    def test_one_of_the_two_is_highlighted(self):
        response = self.client.get('/kolo/')

        self.assertContains(response, 'is-suggested', count=1)


class AdminTimetablePageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.scheduler = User.objects.create_user(
            username='scheduler', email='s@test.com', password=PASSWORD, is_staff=True,
        )
        cls.scheduler.user_permissions.add(
            Permission.objects.get(codename='change_seminar', content_type__app_label='seminars'),
            Permission.objects.get(codename='view_seminar', content_type__app_label='seminars'),
        )
        cls.onlooker = User.objects.create_user(
            username='onlooker', email='o@test.com', password=PASSWORD, is_staff=True,
        )
        cls.onlooker.user_permissions.add(
            Permission.objects.get(codename='view_seminar', content_type__app_label='seminars'),
        )

    def setUp(self):
        cache.clear()

    def test_the_page_lets_a_scheduler_ask_for_any_week(self):
        self.client.force_login(self.scheduler)

        response = self.client.get(ADMIN_PAGE)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{reverse("calendar-image")}"')
        self.assertContains(response, 'type="date"')

    def test_the_page_also_lists_the_public_weeks(self):
        self.client.force_login(self.scheduler)

        response = self.client.get(ADMIN_PAGE)

        for monday in offered_week_starts():
            self.assertContains(response, f"week={monday.isoformat()}")

    def test_staff_who_cannot_schedule_are_turned_away(self):
        self.client.force_login(self.onlooker)

        self.assertEqual(self.client.get(ADMIN_PAGE).status_code, 403)

    def test_anonymous_callers_are_sent_to_the_login_page(self):
        response = self.client.get(ADMIN_PAGE)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])

    def test_the_seminar_list_links_to_the_page_for_a_scheduler(self):
        self.client.force_login(self.scheduler)

        response = self.client.get('/admin/seminars/seminar/')

        self.assertContains(response, ADMIN_PAGE)

    def test_the_seminar_list_hides_the_link_from_everyone_else(self):
        self.client.force_login(self.onlooker)

        response = self.client.get('/admin/seminars/seminar/')

        self.assertNotContains(response, ADMIN_PAGE)

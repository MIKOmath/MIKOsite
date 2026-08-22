"""The weekly plan as a picture."""
from datetime import date, time, timedelta
from io import BytesIO
from unittest import mock

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import User
from mainSite.models import RegistrationEvent
from mikosite.dates import seconds_until_next_midnight
from olympiads.models import Olympiad, OlympiadStage
from seminars.models import Seminar, SeminarGroup
from seminars.timetable_image import (
    INK_MUTED,
    MAX_EVENTS,
    SURFACE,
    WIDTH,
    _contrast,
    build_week_image,
    get_week_image,
    readable_accent,
    render_week,
    week_image_cache_key,
    week_start_of,
)

IMAGE_URL = '/api/calendar/image/'
PNG_MAGIC = b'\x89PNG\r\n\x1a\n'


def this_monday():
    return week_start_of(timezone.localdate())


def make_seminar(day, start, theme, group=None, **kwargs):
    return Seminar.objects.create(
        date=day,
        time=start,
        duration=timedelta(hours=1, minutes=30),
        theme=theme,
        group=group,
        **kwargs,
    )


def opened(png):
    return Image.open(BytesIO(png))


class TimetableImageWindowTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.monday = this_monday()

    def test_no_week_given_means_the_week_we_are_in(self):
        response = self.client.get(IMAGE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.monday.isoformat(), response['Content-Disposition'])

    def test_every_day_of_a_week_asks_for_the_same_sheet(self):
        etags = set()
        for offset in range(7):
            day = self.monday + timedelta(days=offset)
            response = self.client.get(IMAGE_URL, {'week': day.isoformat()})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            etags.add(response['ETag'])

        self.assertEqual(len(etags), 1)

    def test_the_offered_weeks_are_accepted(self):
        for weeks in (-1, 0, 1, 2):
            with self.subTest(weeks=weeks):
                week = self.monday + timedelta(weeks=weeks)
                response = self.client.get(IMAGE_URL, {'week': week.isoformat()})

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertIn(week.isoformat(), response['Content-Disposition'])

    def test_weeks_outside_the_window_are_refused(self):
        for weeks in (-2, 3):
            with self.subTest(weeks=weeks):
                week = self.monday + timedelta(weeks=weeks)
                response = self.client.get(IMAGE_URL, {'week': week.isoformat()})

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('week', response.data)

    def test_a_refusal_is_readable_json_even_though_a_png_was_asked_for(self):
        response = self.client.get(IMAGE_URL, {'week': '01-03-2026'}, HTTP_ACCEPT='image/png')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_malformed_dates_are_refused(self):
        response = self.client.get(IMAGE_URL, {'week': 'w przyszłym tygodniu'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_the_sheet_is_read_only(self):
        self.assertEqual(self.client.post(IMAGE_URL).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class TimetableImageSchedulerTests(APITestCase):
    """Scheduling seminars widens the range and nothing else: the sheet still
    carries the public rows, and it is never kept."""

    def setUp(self):
        cache.clear()
        self.monday = this_monday()
        self.long_ago = self.monday - timedelta(weeks=20)
        make_seminar(self.long_ago, time(18, 0), "Dawno temu")
        make_seminar(self.monday, time(18, 0), "W tym tygodniu")

        self.member = User.objects.create_user(
            username='member', email='member@test.com', password='Testpass1!',
        )
        self.scheduler = User.objects.create_user(
            username='scheduler', email='scheduler@test.com', password='Testpass1!',
        )
        self.scheduler.user_permissions.add(
            Permission.objects.get(codename='change_seminar', content_type__app_label='seminars'),
        )
        self.adder = User.objects.create_user(
            username='adder', email='adder@test.com', password='Testpass1!',
        )
        self.adder.user_permissions.add(
            Permission.objects.get(codename='add_seminar', content_type__app_label='seminars'),
        )
        self.admin = User.objects.create_superuser(
            username='admin', email='admin@test.com', password='Testpass1!',
        )

    def ask_for_the_old_week(self):
        return self.client.get(IMAGE_URL, {'week': self.long_ago.isoformat()})

    def test_the_public_may_not_reach_beyond_the_window(self):
        for user in (None, self.member):
            with self.subTest(user=user):
                self.client.force_authenticate(user)

                self.assertEqual(self.ask_for_the_old_week().status_code,
                                 status.HTTP_400_BAD_REQUEST)

    def test_permission_to_change_a_seminar_opens_the_whole_calendar(self):
        self.client.force_authenticate(self.scheduler)

        response = self.ask_for_the_old_week()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'image/png')

    def test_permission_to_add_a_seminar_opens_it_too(self):
        self.client.force_authenticate(self.adder)

        self.assertEqual(self.ask_for_the_old_week().status_code, status.HTTP_200_OK)

    def test_an_administrator_needs_no_permission_granted_to_them(self):
        self.client.force_authenticate(self.admin)

        self.assertEqual(self.ask_for_the_old_week().status_code, status.HTTP_200_OK)

    def test_an_api_key_carries_the_permission_just_as_a_login_does(self):
        token = Token.objects.create(user=self.scheduler)

        response = self.client.get(IMAGE_URL, {'week': self.long_ago.isoformat()},
                                   HTTP_AUTHORIZATION=f'Token {token.key}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_a_week_off_the_window_is_drawn_to_order_and_not_kept(self):
        self.client.force_authenticate(self.scheduler)

        with mock.patch.object(cache, 'set', wraps=cache.set) as recorded:
            response = self.ask_for_the_old_week()

        self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(
            [call.args[0] for call in recorded.call_args_list if 'timetable-image' in call.args[0]],
            [],
        )
        self.assertIsNone(cache.get(week_image_cache_key(self.long_ago)))

    def test_a_week_inside_the_window_is_still_the_shared_sheet(self):
        self.client.force_authenticate(self.scheduler)

        response = self.client.get(IMAGE_URL)

        self.assertIn('public', response['Cache-Control'])
        self.assertEqual(response.content, get_week_image(self.monday)[0])

    def test_the_wider_range_does_not_hand_over_what_is_unpublished(self):
        RegistrationEvent.objects.create(
            name="Zjazd ukryty",
            location="Warszawa",
            date_begin=self.long_ago,
            date_end=self.long_ago + timedelta(days=2),
            registration_begin=self.long_ago - timedelta(days=30),
            registration_end=self.long_ago - timedelta(days=1),
            registration_url='https://example.invalid/',
            is_published=False,
        )
        self.client.force_authenticate(self.scheduler)

        response = self.ask_for_the_old_week()

        self.assertEqual(response.content, build_week_image(self.long_ago))
        self.assertNotEqual(response.content,
                            build_week_image(self.long_ago, include_unpublished=True))


class TimetableImageResponseTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.monday = this_monday()
        self.group = SeminarGroup.objects.create(name="OM średnia", short_label="OM śr.", color="#0E7C9B")
        make_seminar(self.monday, time(18, 0), "Nierówności", group=self.group)

    def test_the_body_is_a_png_of_the_advertised_width(self):
        response = self.client.get(IMAGE_URL)

        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertTrue(response.content.startswith(PNG_MAGIC))
        self.assertEqual(opened(response.content).width, WIDTH)

    def test_the_sheet_may_be_cached_by_whoever_receives_it(self):
        response = self.client.get(IMAGE_URL)

        self.assertIn('public', response['Cache-Control'])
        self.assertIn('max-age=', response['Cache-Control'])

    def test_a_known_etag_saves_sending_the_bytes_again(self):
        first = self.client.get(IMAGE_URL)

        second = self.client.get(IMAGE_URL, HTTP_IF_NONE_MATCH=first['ETag'])

        self.assertEqual(second.status_code, status.HTTP_304_NOT_MODIFIED)
        self.assertEqual(second.content, b'')
        self.assertEqual(second['ETag'], first['ETag'])

    def test_a_weakened_etag_counts_as_the_same_sheet(self):
        """A proxy is free to hand the tag back weakened, and often does."""
        first = self.client.get(IMAGE_URL)

        second = self.client.get(IMAGE_URL, HTTP_IF_NONE_MATCH=f'W/{first["ETag"]}')

        self.assertEqual(second.status_code, status.HTTP_304_NOT_MODIFIED)

    def test_a_stale_etag_still_gets_the_sheet(self):
        response = self.client.get(IMAGE_URL, HTTP_IF_NONE_MATCH='"nieaktualny"')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_the_download_is_named_after_the_week(self):
        response = self.client.get(IMAGE_URL)

        self.assertEqual(
            response['Content-Disposition'],
            f'inline; filename="miko-plan-{self.monday.isoformat()}.png"',
        )

    def test_the_png_suffix_route_serves_the_same_sheet(self):
        suffixed = self.client.get('/api/calendar/image.png')

        self.assertEqual(suffixed.status_code, status.HTTP_200_OK)
        self.assertEqual(suffixed.content, self.client.get(IMAGE_URL).content)

    def test_a_head_request_answers_with_the_headers_alone(self):
        response = self.client.head(IMAGE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'image/png')


class TimetableImageCacheTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.monday = this_monday()
        make_seminar(self.monday, time(18, 0), "Nierówności")

    def test_a_second_request_costs_no_queries(self):
        self.client.get(IMAGE_URL)

        with self.assertNumQueries(0):
            self.client.get(IMAGE_URL)

    def test_editing_the_calendar_redraws_the_sheet(self):
        before = self.client.get(IMAGE_URL).content

        make_seminar(self.monday + timedelta(days=1), time(20, 0), "Dodane później")

        self.assertNotEqual(self.client.get(IMAGE_URL).content, before)

    def test_a_redrawn_sheet_replaces_the_old_one_instead_of_joining_it(self):
        with mock.patch.object(cache, 'set', wraps=cache.set) as recorded:
            self.client.get(IMAGE_URL)
            make_seminar(self.monday, time(20, 0), "Kolejne")
            self.client.get(IMAGE_URL)

        written = {call.args[0] for call in recorded.call_args_list if 'timetable-image' in call.args[0]}
        self.assertEqual(written, {week_image_cache_key(self.monday)})

    def test_no_sheet_outlives_the_day_it_marks(self):
        with mock.patch.object(cache, 'set', wraps=cache.set) as recorded:
            self.client.get(IMAGE_URL)

        lifetimes = [call.args[2] for call in recorded.call_args_list if 'timetable-image' in call.args[0]]
        self.assertTrue(lifetimes)
        for lifetime in lifetimes:
            self.assertLessEqual(lifetime, seconds_until_next_midnight())

    def test_only_the_week_asked_for_is_kept(self):
        self.client.get(IMAGE_URL)

        self.assertIsNotNone(cache.get(week_image_cache_key(self.monday)))
        self.assertIsNone(cache.get(week_image_cache_key(self.monday + timedelta(weeks=1))))

    def test_the_calendar_payload_is_not_cached_alongside_the_sheet(self):
        # A week held as JSON as well as pixels would be the same week twice.
        with mock.patch.object(cache, 'set', wraps=cache.set) as recorded:
            self.client.get(IMAGE_URL)

        written = [call.args[0] for call in recorded.call_args_list]
        self.assertEqual([key for key in written if key.startswith('calendar-payload:')], [])


class TimetableImagePlaneTests(APITestCase):
    """The sheet is a view onto the calendar, so it obeys the same two planes."""

    def setUp(self):
        cache.clear()
        self.monday = this_monday()
        self.admin = User.objects.create_superuser(
            username='admin', email='admin@test.com', password='Testpass1!',
        )
        self.member = User.objects.create_user(
            username='member', email='member@test.com', password='Testpass1!',
        )
        make_seminar(self.monday, time(18, 0), "Nierówności")
        self.hidden_event = RegistrationEvent.objects.create(
            name="Zjazd ukryty",
            location="Warszawa",
            date_begin=self.monday + timedelta(days=1),
            date_end=self.monday + timedelta(days=2),
            registration_begin=self.monday - timedelta(days=30),
            registration_end=self.monday - timedelta(days=1),
            registration_url='https://example.invalid/',
            is_published=False,
        )

    def test_the_public_sheet_leaves_out_what_is_switched_off(self):
        published = build_week_image(self.monday)
        previewed = build_week_image(self.monday, include_unpublished=True)

        self.assertNotEqual(published, previewed)

    def test_an_administrator_previews_what_is_switched_off(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get(IMAGE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, build_week_image(self.monday, include_unpublished=True))

    def test_an_administrator_preview_is_never_handed_on(self):
        self.client.force_authenticate(self.admin)
        admin_sheet = self.client.get(IMAGE_URL)

        self.assertIn('no-store', admin_sheet['Cache-Control'])
        self.assertIn('Cookie', admin_sheet['Vary'])

        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(IMAGE_URL).content, build_week_image(self.monday))

    def test_a_member_is_served_the_public_sheet(self):
        self.client.force_authenticate(self.member)

        self.assertEqual(self.client.get(IMAGE_URL).content, build_week_image(self.monday))

    def test_publishing_an_event_redraws_the_public_sheet(self):
        before = self.client.get(IMAGE_URL).content

        self.hidden_event.is_published = True
        self.hidden_event.save()

        self.assertNotEqual(self.client.get(IMAGE_URL).content, before)


class TimetableRenderTests(TestCase):
    """The drawing has to survive whatever the calendar holds."""

    def setUp(self):
        cache.clear()
        self.monday = date(2026, 3, 2)

    def render(self, **payload):
        return render_week(
            {'seminars': [], 'registration_events': [], 'olympiad_stages': [], **payload},
            self.monday,
            today=self.monday,
        )

    def seminar(self, day_offset=0, theme="Nierówności", tutors=(), group=None):
        return {
            'id': day_offset,
            'date': (self.monday + timedelta(days=day_offset)).isoformat(),
            'time': '18:00',
            'time_label': '18:00-19:30',
            'theme': theme,
            'tutors': list(tutors),
            'group': group,
        }

    def test_an_empty_week_still_draws_a_sheet(self):
        image = opened(self.render())

        self.assertEqual(image.width, WIDTH)
        self.assertGreaterEqual(image.height, WIDTH)

    def test_a_seminar_without_tutors_or_a_group_draws(self):
        self.assertTrue(self.render(seminars=[self.seminar()]).startswith(PNG_MAGIC))

    def test_a_very_long_theme_does_not_widen_the_sheet(self):
        long_theme = "Nierówności " * 40

        image = opened(self.render(seminars=[self.seminar(theme=long_theme)]))

        self.assertEqual(image.width, WIDTH)

    def test_an_unbroken_word_longer_than_the_card_is_clipped(self):
        image = opened(self.render(seminars=[self.seminar(theme="a" * 400)]))

        self.assertEqual(image.width, WIDTH)

    def test_a_week_beyond_the_cap_stops_growing(self):
        crowd = [self.seminar(day_offset=index % 7, theme=f"Spotkanie {index}")
                 for index in range(MAX_EVENTS * 3)]

        capped = opened(self.render(seminars=crowd))
        at_the_cap = opened(self.render(seminars=crowd[:MAX_EVENTS]))

        # Only the overflow line separates them, not another two hundred cards.
        self.assertLess(capped.height - at_the_cap.height, 200)

    def test_a_multi_day_entry_takes_room_of_its_own(self):
        band = {
            'kind': 'registration_event', 'title': "Zjazd MIKO",
            'date_begin': self.monday.isoformat(),
            'date_end': (self.monday + timedelta(days=2)).isoformat(),
            'date_range': "2-4 marca",
        }
        # Enough seminars that the sheet is taller than its minimum either way.
        week = [self.seminar(day_offset=offset) for offset in range(7)]

        without = opened(self.render(seminars=week))
        with_band = opened(self.render(seminars=week, registration_events=[band]))

        self.assertGreater(with_band.height, without.height)


class GroupColourTests(TestCase):
    """Group colours are picked for the white calendar, not for a dark sheet."""

    def test_the_default_group_colour_is_lifted_off_the_card(self):
        self.assertGreaterEqual(_contrast(readable_accent(SURFACE), SURFACE), 2.0)

    def test_a_bright_group_colour_is_left_alone(self):
        self.assertEqual(readable_accent('#F24535'), '#F24535')

    def test_a_seminar_with_no_group_still_gets_a_stripe(self):
        self.assertEqual(readable_accent(None), INK_MUTED)


class WeekImageHelperTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_a_monday_is_its_own_week_start(self):
        monday = date(2026, 3, 2)

        self.assertEqual(week_start_of(monday), monday)
        self.assertEqual(week_start_of(date(2026, 3, 8)), monday)

    def test_the_sheet_is_drawn_once_and_then_read_back(self):
        monday = this_monday()
        make_seminar(monday, time(18, 0), "Nierówności")

        first_png, first_etag = get_week_image(monday)
        with self.assertNumQueries(0):
            second_png, second_etag = get_week_image(monday)

        self.assertEqual(first_png, second_png)
        self.assertEqual(first_etag, second_etag)


class OlympiadStageOnTheSheetTests(TestCase):
    def setUp(self):
        cache.clear()
        self.monday = this_monday()

    def test_a_stage_that_began_before_monday_is_still_drawn(self):
        olympiad = Olympiad.objects.get(name="Olimpiada Matematyczna")
        OlympiadStage.objects.create(
            olympiad=olympiad, name="II etap",
            date_begin=self.monday - timedelta(days=3),
            date_end=self.monday + timedelta(days=3),
        )

        with_stage = build_week_image(self.monday)
        OlympiadStage.objects.all().delete()
        without = build_week_image(self.monday)

        self.assertNotEqual(with_stage, without)

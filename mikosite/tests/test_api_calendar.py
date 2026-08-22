from datetime import date, time, timedelta

from django.core.cache import cache
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from mainSite.models import RegistrationEvent
from olympiads.models import Olympiad, OlympiadStage
from seminars.calendar_data import build_calendar_payload
from seminars.models import DEFAULT_GROUP_COLOR, Seminar, SeminarGroup

CALENDAR_URL = '/api/calendar/'
MARCH = {'start_date': '2026-03-01', 'end_date': '2026-03-31'}


def make_seminar(day, start, theme, group=None, **kwargs):
    return Seminar.objects.create(
        date=day,
        time=start,
        duration=timedelta(hours=1, minutes=30),
        theme=theme,
        group=group,
        **kwargs,
    )


def make_registration_event(name, date_begin, date_end, registration_begin, registration_end, **kwargs):
    return RegistrationEvent.objects.create(
        name=name,
        location=kwargs.pop('location', 'Warszawa'),
        date_begin=date_begin,
        date_end=date_end,
        registration_begin=registration_begin,
        registration_end=registration_end,
        registration_url=kwargs.pop('registration_url', 'https://example.invalid/'),
        **kwargs,
    )


def march_payload():
    return build_calendar_payload(date(2026, 3, 1), date(2026, 3, 31))


class CalendarSeminarPayloadTests(TestCase):
    def setUp(self):
        cache.clear()
        self.group = SeminarGroup.objects.create(
            name="OM średnia",
            short_label="OM śr.",
            color="#0E7C9B",
            default_difficulty=2,
        )
        self.group_without_color = SeminarGroup.objects.create(name="Harmonia")

    def test_seminar_carries_group_colour_and_short_label(self):
        make_seminar(date(2026, 3, 10), time(18, 0), "Nierówności", group=self.group)

        seminar = march_payload()['seminars'][0]

        self.assertEqual(seminar['time'], "18:00")
        self.assertEqual(seminar['time_label'], "18:00-19:30")
        self.assertEqual(seminar['group']['short_label'], "OM śr.")
        self.assertEqual(seminar['group']['color'], "#0E7C9B")

    def test_group_without_colour_falls_back_to_the_default(self):
        make_seminar(date(2026, 3, 10), time(18, 0), "Spotkanie", group=self.group_without_color)

        group = march_payload()['seminars'][0]['group']

        self.assertEqual(group['color'], DEFAULT_GROUP_COLOR)
        self.assertEqual(group['short_label'], "Harmonia")

    def test_seminar_without_group_has_no_group_data(self):
        make_seminar(date(2026, 3, 10), time(18, 0), "Spotkanie")

        self.assertIsNone(march_payload()['seminars'][0]['group'])

    def test_seminar_carries_the_badges_shown_in_the_dialog(self):
        tutor = User.objects.create_user(username='tutor', password='Tutorpass1!', email='t@test.com')
        seminar = make_seminar(
            date(2026, 3, 10), time(18, 0), "Geometria",
            group=self.group, featured=True, special_guest=True, description="Opis",
        )
        seminar.tutors.set([tutor])

        payload = march_payload()['seminars'][0]

        self.assertTrue(payload['featured'])
        self.assertTrue(payload['special_guest'])
        self.assertEqual(payload['tutors'], [tutor.full_name])
        self.assertEqual(payload['description'], "Opis")
        self.assertEqual(payload['difficulty_label'], seminar.difficulty_label)

    def test_seminars_are_ordered_by_date_and_time(self):
        make_seminar(date(2026, 3, 10), time(20, 0), "Drugie")
        make_seminar(date(2026, 3, 10), time(18, 0), "Pierwsze")
        make_seminar(date(2026, 3, 11), time(9, 0), "Trzecie")

        self.assertEqual([item['theme'] for item in march_payload()['seminars']],
                         ["Pierwsze", "Drugie", "Trzecie"])

    def test_seminars_outside_the_range_are_left_out(self):
        make_seminar(date(2026, 2, 28), time(18, 0), "Przed")
        make_seminar(date(2026, 3, 10), time(18, 0), "W zakresie")
        make_seminar(date(2026, 4, 1), time(18, 0), "Po")

        self.assertEqual([item['theme'] for item in march_payload()['seminars']], ["W zakresie"])


class CalendarMultiDayPayloadTests(TestCase):
    def setUp(self):
        cache.clear()
        self.olympiad = Olympiad.objects.get(name="Olimpiada Matematyczna")

    def test_registration_event_overlapping_the_range_is_included(self):
        make_registration_event("Zjazd MIKO", date(2026, 2, 26), date(2026, 3, 2),
                                date(2026, 1, 1), date(2026, 2, 20))
        make_registration_event("Obóz po zakresie", date(2026, 4, 1), date(2026, 4, 5),
                                date(2026, 3, 1), date(2026, 3, 20))

        events = march_payload()['registration_events']

        self.assertEqual([event['title'] for event in events], ["Zjazd MIKO"])
        self.assertEqual(events[0]['date_range'], "26 lutego - 2 marca")
        self.assertEqual(events[0]['kind'], 'registration_event')

    def test_registration_window_drives_the_open_flag(self):
        event = make_registration_event("Zjazd MIKO", date(2026, 3, 10), date(2026, 3, 12),
                                        date(2026, 2, 1), date(2026, 3, 1))

        self.assertTrue(event.registration_is_open(today=date(2026, 2, 15)))
        self.assertTrue(event.registration_is_open(today=date(2026, 3, 1)))
        self.assertFalse(event.registration_is_open(today=date(2026, 3, 2)))

    def test_olympiad_stage_is_reported_with_its_olympiad(self):
        OlympiadStage.objects.create(
            olympiad=self.olympiad, name="II etap",
            date_begin=date(2026, 3, 10), date_end=date(2026, 3, 11), location="cała Polska",
        )

        stage = march_payload()['olympiad_stages'][0]

        self.assertEqual(stage['kind'], 'olympiad')
        self.assertEqual(stage['title'], "OM – II etap")
        self.assertEqual(stage['stage_label'], "II etap")
        self.assertEqual(stage['date_range'], "10-11 marca")
        self.assertEqual(stage['location'], "cała Polska")
        self.assertEqual(stage['olympiad']['short_name'], "OM")

    def test_stages_of_inactive_olympiads_are_hidden(self):
        hidden = Olympiad.objects.create(name="Olimpiada Ukryta", short_name="OU", is_active=False)
        OlympiadStage.objects.create(olympiad=hidden, name="Finał",
                                     date_begin=date(2026, 3, 10), date_end=date(2026, 3, 11))

        self.assertEqual(march_payload()['olympiad_stages'], [])

    def test_multi_day_entries_spanning_the_whole_range_are_included(self):
        make_registration_event("Długie zapisy", date(2026, 1, 1), date(2026, 12, 31),
                                date(2026, 1, 1), date(2026, 1, 5))

        self.assertEqual(len(march_payload()['registration_events']), 1)


class CalendarCacheTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.group = SeminarGroup.objects.create(name="OM średnia", short_label="OM śr.")
        make_seminar(date(2026, 3, 10), time(18, 0), "W zakresie", group=self.group)

    def themes(self):
        return [item['theme'] for item in self.client.get(CALENDAR_URL, MARCH).data['seminars']]

    def test_repeated_requests_are_served_from_the_cache(self):
        self.client.get(CALENDAR_URL, MARCH)

        with self.assertNumQueries(0):
            self.client.get(CALENDAR_URL, MARCH)

    def test_query_count_does_not_grow_with_the_number_of_seminars(self):
        tutor = User.objects.create_user(username='tutor', password='Tutorpass1!', email='t@test.com')
        Seminar.objects.first().tutors.set([tutor])

        with self.assertNumQueries(4):
            build_calendar_payload(date(2026, 3, 1), date(2026, 3, 31))

        for day in range(11, 21):
            make_seminar(date(2026, 3, day), time(18, 0), f"Kolejne {day}", group=self.group).tutors.set([tutor])

        with self.assertNumQueries(4):
            build_calendar_payload(date(2026, 3, 1), date(2026, 3, 31))

    def test_saving_a_seminar_invalidates_the_cache(self):
        self.themes()

        make_seminar(date(2026, 3, 11), time(18, 0), "Dodane później")

        self.assertIn("Dodane później", self.themes())

    def test_renaming_a_group_invalidates_the_cache(self):
        self.client.get(CALENDAR_URL, MARCH)

        self.group.short_label = "nowa"
        self.group.save()

        groups = [item['group']['short_label'] for item in self.client.get(CALENDAR_URL, MARCH).data['seminars']]
        self.assertEqual(groups, ["nowa"])

    def test_changing_tutors_invalidates_the_cache(self):
        tutor = User.objects.create_user(username='tutor', password='Tutorpass1!', email='t@test.com')
        self.client.get(CALENDAR_URL, MARCH)

        Seminar.objects.first().tutors.set([tutor])

        tutors = self.client.get(CALENDAR_URL, MARCH).data['seminars'][0]['tutors']
        self.assertEqual(tutors, [tutor.full_name])

    def test_adding_a_registration_event_invalidates_the_cache(self):
        self.client.get(CALENDAR_URL, MARCH)

        make_registration_event("Zjazd MIKO", date(2026, 3, 5), date(2026, 3, 7),
                                date(2026, 2, 1), date(2026, 3, 1))

        response = self.client.get(CALENDAR_URL, MARCH)
        self.assertEqual(len(response.data['registration_events']), 1)

    def test_adding_an_olympiad_stage_invalidates_the_cache(self):
        self.client.get(CALENDAR_URL, MARCH)

        OlympiadStage.objects.create(
            olympiad=Olympiad.objects.get(name="Olimpiada Matematyczna"), name="Finał",
            date_begin=date(2026, 3, 20), date_end=date(2026, 3, 22),
        )

        response = self.client.get(CALENDAR_URL, MARCH)
        self.assertEqual(len(response.data['olympiad_stages']), 1)

    def test_deactivating_an_olympiad_invalidates_the_cache(self):
        olympiad = Olympiad.objects.get(name="Olimpiada Matematyczna")
        OlympiadStage.objects.create(olympiad=olympiad, name="Finał",
                                     date_begin=date(2026, 3, 20), date_end=date(2026, 3, 22))
        self.client.get(CALENDAR_URL, MARCH)

        olympiad.is_active = False
        olympiad.save()

        response = self.client.get(CALENDAR_URL, MARCH)
        self.assertEqual(response.data['olympiad_stages'], [])


class CalendarViewTests(APITestCase):
    def setUp(self):
        cache.clear()
        make_seminar(date(2026, 3, 10), time(18, 0), "W zakresie")

    def test_anonymous_users_can_read_the_calendar(self):
        response = self.client.get(CALENDAR_URL, MARCH)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['start_date'], '2026-03-01')
        self.assertEqual(response.data['end_date'], '2026-03-31')
        self.assertEqual([item['theme'] for item in response.data['seminars']], ["W zakresie"])

    def test_missing_dates_are_rejected(self):
        self.assertEqual(self.client.get(CALENDAR_URL).status_code, status.HTTP_400_BAD_REQUEST)

    def test_malformed_dates_are_rejected(self):
        response = self.client.get(CALENDAR_URL, {'start_date': '01-03-2026', 'end_date': '2026-03-31'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reversed_range_is_rejected(self):
        response = self.client.get(CALENDAR_URL, {'start_date': '2026-03-31', 'end_date': '2026-03-01'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_overly_wide_range_is_rejected(self):
        response = self.client.get(CALENDAR_URL, {'start_date': '2026-01-01', 'end_date': '2026-12-31'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_six_week_grid_range_is_accepted(self):
        response = self.client.get(CALENDAR_URL, {'start_date': '2026-02-23', 'end_date': '2026-04-05'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_calendar_is_read_only(self):
        response = self.client.post(CALENDAR_URL, MARCH)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_the_format_suffix_route_serves_the_calendar(self):
        response = self.client.get('/api/calendar.json', MARCH)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['theme'] for item in response.data['seminars']], ["W zakresie"])


class CalendarPlaneTests(APITestCase):
    """The calendar is a view onto the API, so it obeys the same two planes."""

    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_superuser(
            username='admin', email='admin@test.com', password='Testpass1!',
        )
        self.member = User.objects.create_user(
            username='member', email='member@test.com', password='Testpass1!',
        )
        self.olympiad = Olympiad.objects.get(name="Olimpiada Matematyczna")
        self.hidden_event = make_registration_event(
            "Zjazd ukryty", date(2026, 3, 5), date(2026, 3, 7),
            date(2026, 2, 1), date(2026, 3, 1), is_published=False,
        )
        self.hidden_stage = OlympiadStage.objects.create(
            olympiad=self.olympiad, name="Etap ukryty",
            date_begin=date(2026, 3, 10), date_end=date(2026, 3, 11), is_published=False,
        )

    def payload_for(self, user=None):
        self.client.force_authenticate(user)
        return self.client.get(CALENDAR_URL, MARCH).data

    def test_an_unpublished_event_is_hidden_from_the_public(self):
        for user in (None, self.member):
            with self.subTest(user=user):
                self.assertEqual(self.payload_for(user)['registration_events'], [])

    def test_an_unpublished_stage_is_hidden_from_the_public(self):
        for user in (None, self.member):
            with self.subTest(user=user):
                self.assertEqual(self.payload_for(user)['olympiad_stages'], [])

    def test_an_administrator_sees_what_is_switched_off(self):
        payload = self.payload_for(self.admin)

        self.assertEqual([item['title'] for item in payload['registration_events']],
                         ["Zjazd ukryty"])
        self.assertEqual([item['stage_label'] for item in payload['olympiad_stages']],
                         ["Etap ukryty"])

    def test_an_administrator_read_does_not_poison_the_shared_cache(self):
        self.payload_for(self.admin)

        self.assertEqual(self.payload_for(None)['registration_events'], [])

    def test_a_public_read_does_not_hide_rows_from_the_administrator(self):
        self.payload_for(None)

        self.assertEqual(len(self.payload_for(self.admin)['registration_events']), 1)

    def test_publishing_an_event_invalidates_the_cache(self):
        self.assertEqual(self.payload_for(None)['registration_events'], [])

        self.hidden_event.is_published = True
        self.hidden_event.save()

        self.assertEqual(len(self.payload_for(None)['registration_events']), 1)

    def test_publishing_a_stage_invalidates_the_cache(self):
        self.assertEqual(self.payload_for(None)['olympiad_stages'], [])

        self.hidden_stage.is_published = True
        self.hidden_stage.save()

        self.assertEqual(len(self.payload_for(None)['olympiad_stages']), 1)

    def test_the_calendar_carries_the_discord_routing_like_the_resource_does(self):
        group = SeminarGroup.objects.create(name="OM", discord_role_id='111', discord_channel_id='222')
        seminar = make_seminar(date(2026, 3, 12), time(18, 0), "Nierówności",
                               group=group, discord_channel_id='333')

        embedded = next(
            item for item in self.client.get(CALENDAR_URL, MARCH).data['seminars']
            if item['id'] == seminar.pk
        )

        self.assertEqual(embedded['discord_channel_id'], '333')
        self.assertEqual(embedded['group_role_id'], '111')


class CalendarMatchesTheResourceEndpointsTests(APITestCase):
    """The merge is only real if both routes describe a thing identically."""

    def setUp(self):
        cache.clear()
        self.group = SeminarGroup.objects.create(name="OM średnia", short_label="OM śr.")
        self.seminar = make_seminar(date(2026, 3, 10), time(18, 0), "Nierówności", group=self.group)
        self.event = make_registration_event(
            "Zjazd MIKO", date(2026, 3, 5), date(2026, 3, 7), date(2026, 2, 1), date(2026, 3, 1),
        )
        self.stage = OlympiadStage.objects.create(
            olympiad=Olympiad.objects.get(name="Olimpiada Matematyczna"), name="II etap",
            date_begin=date(2026, 3, 10), date_end=date(2026, 3, 11),
        )

    def test_a_seminar_reads_the_same_either_way(self):
        embedded = self.client.get(CALENDAR_URL, MARCH).data['seminars'][0]
        standalone = self.client.get(f'/api/seminars/{self.seminar.pk}/').data

        self.assertEqual(set(embedded), set(standalone))
        self.assertEqual(embedded['time_label'], standalone['time_label'])
        self.assertEqual(embedded['group'], standalone['group'])

    def test_a_registration_event_reads_the_same_either_way(self):
        embedded = self.client.get(CALENDAR_URL, MARCH).data['registration_events'][0]
        standalone = self.client.get(f'/api/registration-events/{self.event.pk}/').data

        self.assertEqual(set(embedded), set(standalone))
        self.assertEqual(embedded['date_range'], standalone['date_range'])

    def test_an_olympiad_stage_reads_the_same_either_way(self):
        embedded = self.client.get(CALENDAR_URL, MARCH).data['olympiad_stages'][0]
        standalone = self.client.get(f'/api/olympiad-stages/{self.stage.pk}/').data

        self.assertEqual(set(embedded), set(standalone))
        self.assertEqual(embedded['title'], standalone['title'])

"""Seminars and their groups: one shape for the public, one for administrators."""
from datetime import date, time, timedelta

from rest_framework import status

from seminars.models import GoogleFormsTemplate, Seminar, SeminarGroup

from .api_base import ApiPlaneTestCase

PUBLIC_SEMINAR_FIELDS = {
    'id', 'date', 'time', 'time_label', 'duration', 'theme', 'description', 'image', 'file',
    'started', 'finished', 'featured', 'special_guest', 'difficulty', 'difficulty_label',
    'difficulty_icon', 'tutors', 'group', 'discord_channel_id', 'discord_voice_channel_id',
    'group_role_id',
}
ADMIN_SEMINAR_FIELDS = {
    'id', 'date', 'time', 'duration', 'theme', 'description', 'image', 'file', 'started',
    'finished', 'featured', 'special_guest', 'difficulty', 'group', 'form', 'tutors',
    'discord_channel_id', 'discord_voice_channel_id',
}
# The registration form points at an internal template, so it stays admin-only.
# The Discord ids do not: they are public routing.
SEMINAR_SECRETS = {'form'}

PUBLIC_GROUP_FIELDS = {
    'id', 'name', 'short_label', 'color', 'lead', 'description', 'default_difficulty',
    'discord_role_id', 'discord_channel_id', 'discord_voice_channel_id',
}


def make_seminar(day, start, theme, **kwargs):
    return Seminar.objects.create(
        date=day, time=start, duration=timedelta(hours=1, minutes=30), theme=theme, **kwargs,
    )


class SeminarReadTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.group = SeminarGroup.objects.create(
            name="OM średnia", short_label="OM śr.", color="#0E7C9B",
            default_difficulty=2, discord_role_id='111', discord_channel_id='222',
            discord_voice_channel_id='333',
        )
        cls.form = GoogleFormsTemplate.objects.create(name="Zapisy", file='google_forms_templates/f.txt')
        cls.seminar = make_seminar(
            date(2026, 3, 10), time(18, 0), "Nierówności",
            group=cls.group, form=cls.form, discord_channel_id='444',
            discord_voice_channel_id='555', description="Opis",
        )
        cls.seminar.tutors.set([cls.member])

    def test_anyone_may_read_seminars(self):
        response = self.client.get('/api/seminars/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_the_public_shape_is_exactly_the_display_shape(self):
        response = self.client.get(f'/api/seminars/{self.seminar.pk}/')

        self.assertEqual(set(response.data), PUBLIC_SEMINAR_FIELDS)

    def test_the_public_shape_withholds_the_registration_form(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                response = self.client.get(f'/api/seminars/{self.seminar.pk}/')
                self.assertEqual(set(response.data) & SEMINAR_SECRETS, set())

    def test_the_public_shape_carries_the_discord_routing(self):
        response = self.client.get(f'/api/seminars/{self.seminar.pk}/')

        self.assertEqual(response.data['discord_channel_id'], '444')
        self.assertEqual(response.data['discord_voice_channel_id'], '555')
        self.assertEqual(response.data['group_role_id'], '111')

    def test_a_seminar_without_its_own_channel_inherits_the_groups(self):
        bare = make_seminar(date(2026, 3, 11), time(18, 0), "Bez kanału", group=self.group)

        response = self.client.get(f'/api/seminars/{bare.pk}/')

        self.assertEqual(response.data['discord_channel_id'], '222')
        self.assertEqual(response.data['discord_voice_channel_id'], '333')

    def test_a_seminar_without_a_group_reports_no_role(self):
        orphan = make_seminar(date(2026, 3, 12), time(18, 0), "Bez grupy")

        response = self.client.get(f'/api/seminars/{orphan.pk}/')

        self.assertIsNone(response.data['group_role_id'])
        self.assertIsNone(response.data['group'])

    def test_the_nested_group_stays_the_compact_badge(self):
        response = self.client.get(f'/api/seminars/{self.seminar.pk}/')

        self.assertEqual(set(response.data['group']), {'id', 'name', 'short_label', 'color'})

    def test_the_administrator_shape_carries_the_routing_and_the_form(self):
        self.as_admin()

        response = self.client.get(f'/api/seminars/{self.seminar.pk}/')

        self.assertEqual(set(response.data), ADMIN_SEMINAR_FIELDS)
        self.assertEqual(response.data['discord_channel_id'], '444')
        self.assertEqual(response.data['form'], self.form.pk)

    def test_the_time_stays_in_the_form_the_calendar_prints(self):
        response = self.client.get(f'/api/seminars/{self.seminar.pk}/')

        self.assertEqual(response.data['time'], "18:00")
        self.assertEqual(response.data['time_label'], "18:00-19:30")

    def test_tutors_are_named_rather_than_numbered(self):
        response = self.client.get(f'/api/seminars/{self.seminar.pk}/')

        self.assertEqual(response.data['tutors'], [self.member.full_name])

    def test_the_difficulty_falls_back_to_the_groups_default(self):
        response = self.client.get(f'/api/seminars/{self.seminar.pk}/')

        self.assertEqual(response.data['difficulty_label'], "poziom średni")

    def test_the_old_display_only_switch_is_gone_and_harmless(self):
        plain = self.client.get(f'/api/seminars/{self.seminar.pk}/').data
        legacy = self.client.get(f'/api/seminars/{self.seminar.pk}/', {'display_only': '1'}).data

        self.assertEqual(plain, legacy)


class SeminarQueryCountTests(ApiPlaneTestCase):
    def test_the_group_and_tutors_are_joined_rather_than_fetched_per_row(self):
        group = SeminarGroup.objects.create(name="OM")
        for day in range(1, 11):
            make_seminar(date(2026, 3, day), time(18, 0), f"Temat {day}", group=group).tutors.set(
                [self.member],
            )

        with self.assertNumQueries(3):  # count, page of seminars, prefetched tutors
            self.client.get('/api/seminars/')


class SeminarFilterTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.group = SeminarGroup.objects.create(name="OM")
        make_seminar(date(2026, 3, 1), time(18, 0), "Marzec", group=cls.group)
        make_seminar(date(2026, 4, 1), time(18, 0), "Kwiecień")

    def themes(self, params):
        return [item['theme'] for item in self.client.get('/api/seminars/', params).data['results']]

    def test_the_date_window_filters_both_ends(self):
        self.assertEqual(self.themes({'start_date': '2026-03-15'}), ["Kwiecień"])
        self.assertEqual(self.themes({'end_date': '2026-03-15'}), ["Marzec"])

    def test_seminars_may_be_narrowed_to_one_group(self):
        self.assertEqual(self.themes({'group': self.group.pk}), ["Marzec"])

    def test_an_exact_date_may_be_asked_for(self):
        self.assertEqual(self.themes({'date': '2026-04-01'}), ["Kwiecień"])

    def test_an_unknown_query_parameter_is_ignored_rather_than_obeyed(self):
        self.assertEqual(len(self.themes({'nonsense': 'x'})), 2)

    def test_seminars_come_back_in_calendar_order(self):
        self.assertEqual(self.themes({}), ["Marzec", "Kwiecień"])


class SeminarWriteTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.seminar = make_seminar(date(2026, 3, 10), time(18, 0), "Nierówności")

    def payload(self):
        return {
            'date': '2026-05-01', 'time': '18:00', 'duration': '01:30:00', 'theme': "Nowy",
        }

    def test_writing_is_refused_off_the_administrator_plane(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                self.assertEqual(
                    self.client.post('/api/seminars/', self.payload()).status_code,
                    status.HTTP_403_FORBIDDEN,
                )
                self.assertEqual(
                    self.client.patch(f'/api/seminars/{self.seminar.pk}/', {'theme': "X"}).status_code,
                    status.HTTP_403_FORBIDDEN,
                )
                self.assertEqual(
                    self.client.delete(f'/api/seminars/{self.seminar.pk}/').status_code,
                    status.HTTP_403_FORBIDDEN,
                )

    def test_an_administrator_may_create_and_edit_and_delete(self):
        self.as_admin()

        self.assertEqual(
            self.client.post('/api/seminars/', self.payload()).status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            self.client.patch(f'/api/seminars/{self.seminar.pk}/', {'theme': "Zmienione"}).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.client.delete(f'/api/seminars/{self.seminar.pk}/').status_code,
            status.HTTP_204_NO_CONTENT,
        )


class SeminarGroupTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.group = SeminarGroup.objects.create(
            name="OM średnia", lead="Wstęp", description="Opis",
            discord_role_id='111', discord_channel_id='222', discord_voice_channel_id='333',
        )

    def test_anyone_may_read_the_groups(self):
        response = self.client.get('/api/seminar-groups/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data['results'][0]), PUBLIC_GROUP_FIELDS)

    def test_the_public_shape_carries_the_discord_routing(self):
        response = self.client.get(f'/api/seminar-groups/{self.group.pk}/')

        self.assertEqual(response.data['discord_role_id'], '111')
        self.assertEqual(response.data['discord_channel_id'], '222')
        self.assertEqual(response.data['discord_voice_channel_id'], '333')

    def test_the_public_shape_resolves_the_display_defaults(self):
        response = self.client.get(f'/api/seminar-groups/{self.group.pk}/')

        self.assertEqual(response.data['short_label'], "OM średnia")
        self.assertEqual(response.data['color'], "#074A59")

    def test_the_administrator_shape_reports_the_display_defaults_unresolved(self):
        self.as_admin()

        response = self.client.get(f'/api/seminar-groups/{self.group.pk}/')

        self.assertEqual(response.data['short_label'], '')
        self.assertEqual(response.data['color'], '')

    def test_only_administrators_may_write_a_group(self):
        self.as_staff()
        self.assertEqual(
            self.client.post('/api/seminar-groups/', {'name': "Nowa"}).status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.as_admin()
        self.assertEqual(
            self.client.post('/api/seminar-groups/', {'name': "Nowa"}).status_code,
            status.HTTP_201_CREATED,
        )


class InternalResourceTests(ApiPlaneTestCase):
    """Form templates and reminders have no public shape at all."""

    def test_form_templates_are_administrators_only(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                self.assertEqual(
                    self.client.get('/api/google-form-template/').status_code,
                    status.HTTP_403_FORBIDDEN,
                )

    def test_reminders_are_administrators_only(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                self.assertEqual(
                    self.client.get('/api/reminders/').status_code, status.HTTP_403_FORBIDDEN,
                )


class ReminderScheduleTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        from django.utils import timezone

        from seminars.models import Reminder

        cls.seminar = make_seminar(date(2026, 3, 10), time(18, 0), "Nierówności")
        now = timezone.now()
        cls.past = Reminder.objects.create(
            seminar=cls.seminar, type='start', date_time=now - timedelta(hours=1),
        )
        cls.next_one = Reminder.objects.create(
            seminar=cls.seminar, type='start', date_time=now + timedelta(hours=1),
        )
        cls.also_next = Reminder.objects.create(
            seminar=cls.seminar, type='voice', date_time=cls.next_one.date_time,
        )
        cls.later = Reminder.objects.create(
            seminar=cls.seminar, type='start', date_time=now + timedelta(hours=5),
        )

    def test_only_next_returns_everything_due_at_the_same_moment(self):
        self.as_admin()

        response = self.client.get('/api/reminders/', {'only_next': '1'})

        self.assertEqual({item['id'] for item in response.data['results']},
                         {self.next_one.pk, self.also_next.pk})

    def test_without_the_switch_the_whole_schedule_comes_back(self):
        from seminars.models import Reminder

        self.as_admin()

        response = self.client.get('/api/reminders/')

        # Saving a seminar schedules reminders of its own, so count the table.
        self.assertEqual(response.data['count'], Reminder.objects.count())
        self.assertGreaterEqual(response.data['count'], 4)

    def test_only_next_compares_against_an_aware_now(self):
        """The old implementation compared a naive `datetime.now()` against an
        aware column, which Django only warns about."""
        import warnings

        self.as_admin()

        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            response = self.client.get('/api/reminders/', {'only_next': '1'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

"""The access matrix itself.

Every endpoint, every plane, in one table. If a resource is added without a
deliberate decision about who may read and write it, a row here goes missing.
"""
from datetime import date, datetime, time, timedelta
from datetime import timezone as dt_timezone

from django.contrib import admin as django_admin
from django.core.cache import cache
from rest_framework import status

from accounts.models import ActivityScore, LinkedAccount
from hintBase.models import Problem, ProblemHint, Review
from mainSite.models import Image, Partner, Post, RegistrationEvent
from olympiads.models import Olympiad, OlympiadStage
from seminars.models import (
    GoogleFormsTemplate,
    PreviousEdition,
    PreviousEditionMilestone,
    Reminder,
    Seminar,
    SeminarGroup,
)

from .api_base import ApiPlaneTestCase

CALENDAR = '/api/calendar/?start_date=2026-03-01&end_date=2026-03-31'

PUBLICLY_READABLE = [
    '/api/seminars/',
    '/api/seminar-groups/',
    '/api/posts/',
    '/api/partners/',
    '/api/registration-events/',
    '/api/olympiads/',
    '/api/olympiad-stages/',
    '/api/previous-editions/',
]

ADMIN_ONLY = [
    '/api/users/',
    '/api/linked-accounts/',
    '/api/user-activity/',
    '/api/google-form-template/',
    '/api/reminders/',
]

# Signed in to read your own, administrator to read everyone's.
MEMBER_READABLE = ['/api/activity-scores/']

ALL_WRITABLE = PUBLICLY_READABLE + ADMIN_ONLY + MEMBER_READABLE

EXPECTED_API_ROOT = {
    'calendar', 'seminar-groups', 'seminars', 'previous-editions', 'olympiads',
    'olympiad-stages', 'registration-events', 'partners', 'posts', 'users',
    'linked-accounts', 'user-activity', 'activity-scores',
    'google-form-template', 'reminders',
}


class ApiRootTests(ApiPlaneTestCase):
    def test_the_router_exposes_exactly_the_intended_resources(self):
        response = self.client.get('/api/')

        self.assertEqual(set(response.data), EXPECTED_API_ROOT)

    def test_the_calendar_is_part_of_the_api_root(self):
        self.assertIn('calendar', self.client.get('/api/').data)


class PublicReadPlaneTests(ApiPlaneTestCase):
    def test_anonymous_callers_may_read_the_public_resources(self):
        for url in PUBLICLY_READABLE + [CALENDAR]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)

    def test_members_may_read_the_public_resources(self):
        self.as_member()
        for url in PUBLICLY_READABLE + [CALENDAR]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)


class AdminOnlyPlaneTests(ApiPlaneTestCase):
    def test_anonymous_callers_are_refused(self):
        for url in ADMIN_ONLY + MEMBER_READABLE:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_members_are_refused(self):
        self.as_member()
        for url in ADMIN_ONLY:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_are_refused_because_staff_is_not_an_api_administrator(self):
        self.as_staff()
        for url in ADMIN_ONLY:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_administrators_are_admitted(self):
        self.as_admin()
        for url in ADMIN_ONLY + MEMBER_READABLE:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)


class WritePlaneTests(ApiPlaneTestCase):
    """Writing anywhere in the API is an administrator's act."""

    def test_anonymous_callers_may_not_write(self):
        for url in ALL_WRITABLE:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, {}).status_code, status.HTTP_403_FORBIDDEN)

    def test_members_may_not_write(self):
        self.as_member()
        for url in ALL_WRITABLE:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, {}).status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_may_not_write(self):
        self.as_staff()
        for url in ALL_WRITABLE:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, {}).status_code, status.HTTP_403_FORBIDDEN)

    def test_administrators_are_past_the_permission_gate(self):
        # An empty body is rejected by validation, not by permissions - which is
        # the distinction being asserted.
        self.as_admin()
        for url in ALL_WRITABLE:
            with self.subTest(url=url):
                self.assertNotEqual(self.client.post(url, {}).status_code, status.HTTP_403_FORBIDDEN)

    def test_the_calendar_is_read_only_even_for_administrators(self):
        self.as_admin()

        response = self.client.post('/api/calendar/', {})

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class DefaultPermissionTests(ApiPlaneTestCase):
    def test_a_viewset_that_declares_nothing_is_closed(self):
        from rest_framework.viewsets import ModelViewSet

        from mikosite.permissions import IsAdmin

        self.assertEqual(ModelViewSet.permission_classes, [IsAdmin])


class SecretExposureTests(ApiPlaneTestCase):
    """No response, on any plane, carries a credential or a privilege flag."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cache.clear()
        cls.group = SeminarGroup.objects.create(name="OM", discord_role_id='9', discord_channel_id='8')
        cls.seminar = Seminar.objects.create(
            date=date(2026, 3, 10), time=time(18, 0), duration=timedelta(hours=1),
            theme="Nierówności", group=cls.group, discord_channel_id='7',
        )
        cls.seminar.tutors.set([cls.member])
        post = Post.objects.create(title="Ogłoszenie", date=date(2026, 3, 1), time=time(12, 0))
        post.authors.set([cls.member])
        post.images.set([Image.objects.create(image='post_images/i.webp')])
        Partner.objects.create(name="Partner")
        RegistrationEvent.objects.create(
            name="Zjazd", location="Warszawa",
            date_begin=date(2026, 3, 5), date_end=date(2026, 3, 7),
            registration_begin=date(2026, 2, 1), registration_end=date(2026, 3, 1),
            registration_url='https://example.invalid/',
        )
        OlympiadStage.objects.create(
            olympiad=Olympiad.objects.first(), name="II etap",
            date_begin=date(2026, 3, 10), date_end=date(2026, 3, 11),
        )
        edition = PreviousEdition.objects.create(
            start_date=date(2024, 9, 1), end_date=date(2025, 6, 20), member_count=100,
        )
        PreviousEditionMilestone.objects.create(edition=edition, date=date(2024, 10, 1), title="Start")
        ActivityScore.objects.create(user=cls.member, change=5, reason="obecność")
        LinkedAccount.objects.create(user=cls.member, external_id='123', platform='discord')
        GoogleFormsTemplate.objects.create(name="Formularz", file='google_forms_templates/f.txt')
        Reminder.objects.create(
            seminar=cls.seminar, type='start',
            date_time=datetime(2026, 3, 10, 17, 0, tzinfo=dt_timezone.utc),
        )

    def readable_urls(self):
        return PUBLICLY_READABLE + MEMBER_READABLE + ADMIN_ONLY + [
            CALENDAR,
            '/api/users/me/',
            f'/api/users/{self.member.pk}/',
            f'/api/seminars/{self.seminar.pk}/',
        ]

    def test_nothing_leaks_to_an_administrator(self):
        self.as_admin()
        for url in self.readable_urls():
            with self.subTest(url=url):
                self.assertNoSecretsIn(self.client.get(url).data, url)

    def test_nothing_leaks_to_a_member(self):
        self.as_member()
        for url in PUBLICLY_READABLE + MEMBER_READABLE + [
            CALENDAR, '/api/users/me/', f'/api/users/{self.member.pk}/',
        ]:
            with self.subTest(url=url):
                self.assertNoSecretsIn(self.client.get(url).data, url)

    def test_nothing_leaks_to_an_anonymous_caller(self):
        for url in PUBLICLY_READABLE + [CALENDAR, f'/api/users/{self.member.pk}/']:
            with self.subTest(url=url):
                self.assertNoSecretsIn(self.client.get(url).data, url)

    def test_the_password_hash_is_not_even_loaded_for_a_user_read(self):
        self.as_admin()

        response = self.client.get(f'/api/users/{self.member.pk}/')

        self.assertNotIn('password', response.data)
        self.assertNotIn(self.member.password, str(response.content))


class AuthTokenExposureTests(ApiPlaneTestCase):
    """Tokens authenticate callers; they are never data the API hands back."""

    def test_the_api_offers_no_token_resource(self):
        root = self.client.get('/api/').data

        self.assertFalse([name for name in root if 'token' in name.lower()])

    def test_a_members_token_is_not_reachable_through_their_own_record(self):
        from rest_framework.authtoken.models import Token

        token = Token.objects.create(user=self.member)
        self.as_member()

        response = self.client.get('/api/users/me/')

        self.assertNotIn(token.key, str(response.content))
        self.assertNotIn('auth_token', response.data)

    def test_a_token_authenticates_on_the_plane_of_the_user_behind_it(self):
        from rest_framework.authtoken.models import Token

        member_token = Token.objects.create(user=self.member)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {member_token.key}')

        self.assertEqual(self.client.get('/api/reminders/').status_code, status.HTTP_403_FORBIDDEN)

        admin_token = Token.objects.create(user=self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {admin_token.key}')

        self.assertEqual(self.client.get('/api/reminders/').status_code, status.HTTP_200_OK)


class RetiredEndpointTests(ApiPlaneTestCase):
    def test_the_image_library_has_no_endpoint_of_its_own(self):
        self.as_admin()

        self.assertNotIn('post-images', self.client.get('/api/').data)
        self.assertEqual(
            self.client.get('/api/post-images/').status_code, status.HTTP_404_NOT_FOUND,
        )

    def test_images_are_still_reachable_through_the_posts_that_carry_them(self):
        post = Post.objects.create(title="Ogłoszenie", date=date(2026, 3, 1), time=time(12, 0))
        post.images.set([Image.objects.create(image='post_images/i.webp')])

        response = self.client.get(f'/api/posts/{post.pk}/')

        self.assertIn('i.webp', response.data['images'][0]['image'])


class HintBaseRetirementTests(ApiPlaneTestCase):
    def test_no_hint_base_model_is_registered_in_the_admin_panel(self):
        registered = set(django_admin.site._registry)

        self.assertTrue(registered.isdisjoint({Problem, ProblemHint, Review}))

    def test_no_hint_base_resource_is_routed_in_the_api(self):
        root = self.client.get('/api/').data

        self.assertFalse([name for name in root if 'hint' in name.lower() or 'problem' in name.lower()])

    def test_the_hint_base_pages_are_not_routed(self):
        for url in ('/bazahintow/', '/bazahintow/addproblem/'):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

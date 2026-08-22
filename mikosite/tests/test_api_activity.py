"""Activity scores: a member's own, an administrator's everyone's."""
from datetime import timedelta

from django.utils import timezone
from rest_framework import status

from accounts.models import ActivityScore

from .api_base import ApiPlaneTestCase

OWN_FIELDS = {'id', 'change', 'reason', 'timestamp'}
ADMIN_FIELDS = OWN_FIELDS | {'user'}


class ActivityScoreReadTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.mine = ActivityScore.objects.create(user=cls.member, change=5, reason="obecność")
        cls.theirs = ActivityScore.objects.create(user=cls.staff, change=7, reason="cudze")

    def test_anonymous_callers_may_not_read_scores(self):
        self.assertEqual(
            self.client.get('/api/activity-scores/').status_code, status.HTTP_403_FORBIDDEN,
        )

    def test_a_member_reads_only_their_own(self):
        self.as_member()

        response = self.client.get('/api/activity-scores/')

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['reason'], "obecność")

    def test_a_member_cannot_reach_someone_elses_score_by_id(self):
        self.as_member()

        response = self.client.get(f'/api/activity-scores/{self.theirs.pk}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_a_member_cannot_filter_their_way_to_someone_elses_scores(self):
        self.as_member()

        response = self.client.get('/api/activity-scores/', {'user': str(self.staff.pk)})

        self.assertEqual(response.data['count'], 0)

    def test_a_members_shape_does_not_name_the_member(self):
        self.as_member()

        response = self.client.get('/api/activity-scores/')

        self.assertEqual(set(response.data['results'][0]), OWN_FIELDS)

    def test_an_administrator_reads_every_score_with_its_owner(self):
        self.as_admin()

        response = self.client.get('/api/activity-scores/')

        self.assertEqual(response.data['count'], 2)
        self.assertEqual(set(response.data['results'][0]), ADMIN_FIELDS)

    def test_staff_are_treated_as_ordinary_members_here(self):
        self.as_staff()

        response = self.client.get('/api/activity-scores/')

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['reason'], "cudze")


class ActivityScoreFilterTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        now = timezone.now()
        cls.old = ActivityScore.objects.create(
            user=cls.member, change=1, reason="dawno", timestamp=now - timedelta(days=30),
        )
        cls.recent = ActivityScore.objects.create(
            user=cls.member, change=2, reason="niedawno", timestamp=now,
        )

    def test_an_administrator_may_narrow_to_one_member(self):
        self.as_admin()

        response = self.client.get('/api/activity-scores/', {'user': str(self.member.pk)})

        self.assertEqual(response.data['count'], 2)

    def test_the_timestamp_window_filters_both_ends(self):
        self.as_admin()
        cutoff = (timezone.now() - timedelta(days=1)).isoformat()

        response = self.client.get('/api/activity-scores/', {'start_timestamp': cutoff})

        self.assertEqual([item['reason'] for item in response.data['results']], ["niedawno"])

    def test_an_unknown_query_parameter_is_ignored_rather_than_obeyed(self):
        self.as_admin()

        response = self.client.get('/api/activity-scores/', {'nonsense': 'x'})

        self.assertEqual(response.data['count'], 2)


class ActivityScoreWriteTests(ApiPlaneTestCase):
    def payload(self):
        return {'user': str(self.member.pk), 'change': 4, 'reason': "zadanie"}

    def test_a_member_may_not_award_themselves_points(self):
        self.as_member()

        response = self.client.post('/api/activity-scores/', self.payload())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ActivityScore.objects.count(), 0)

    def test_staff_may_not_award_points(self):
        self.as_staff()

        response = self.client.post('/api/activity-scores/', self.payload())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_an_administrator_may_award_points(self):
        self.as_admin()

        response = self.client.post('/api/activity-scores/', self.payload())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ActivityScore.objects.get().change, 4)


class UserActivityRankingTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        ActivityScore.objects.create(user=cls.member, change=5, reason="a")
        ActivityScore.objects.create(user=cls.member, change=3, reason="b")
        ActivityScore.objects.create(user=cls.staff, change=20, reason="c")

    def test_the_ranking_itself_is_administrators_only(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                self.assertEqual(
                    self.client.get('/api/user-activity/').status_code, status.HTTP_403_FORBIDDEN,
                )

    def test_a_member_may_read_their_own_standing(self):
        self.as_member()

        response = self.client.get(f'/api/user-activity/{self.member.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['activity_score'], 8)
        self.assertEqual(response.data['username'], 'member')

    def test_a_member_may_reach_their_own_standing_without_knowing_their_id(self):
        self.as_member()

        response = self.client.get('/api/user-activity/me/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['activity_score'], 8)

    def test_the_own_standing_is_reachable_through_the_format_suffix_route(self):
        self.as_member()

        response = self.client.get('/api/user-activity/me.json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['activity_score'], 8)

    def test_a_member_may_not_read_someone_elses_standing(self):
        self.as_member()

        response = self.client.get(f'/api/user-activity/{self.staff.pk}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_callers_have_no_standing_to_read(self):
        for url in ('/api/user-activity/me/', f'/api/user-activity/{self.member.pk}/'):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_a_member_with_no_scores_reads_a_zero_rather_than_a_null(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get('/api/user-activity/me/')

        self.assertEqual(response.data['activity_score'], 0)

    def test_a_members_own_standing_is_the_same_number_as_their_profile_reports(self):
        self.as_member()

        standing = self.client.get('/api/user-activity/me/').data['activity_score']
        profile = self.client.get('/api/users/me/').data['activity_score']

        self.assertEqual(standing, profile)

    def test_members_are_ranked_by_their_running_total(self):
        self.as_admin()

        response = self.client.get('/api/user-activity/')

        self.assertEqual([item['username'] for item in response.data['results']],
                         ['staffer', 'member'])
        self.assertEqual([item['activity_score'] for item in response.data['results']], [20, 8])

    def test_members_who_have_never_scored_are_left_out_of_the_ranking(self):
        self.as_admin()

        response = self.client.get('/api/user-activity/')

        self.assertNotIn('admin', [item['username'] for item in response.data['results']])

    def test_one_member_can_still_be_read_even_with_no_scores(self):
        self.as_admin()

        response = self.client.get(f'/api/user-activity/{self.admin.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['activity_score'], 0)

    def test_the_ranking_does_not_aggregate_once_per_row(self):
        self.as_admin()

        with self.assertNumQueries(2):  # count, then the ranked page
            self.client.get('/api/user-activity/')

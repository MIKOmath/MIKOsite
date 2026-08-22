"""Who may see what about a member."""
from rest_framework import status

from accounts.models import ActivityScore, LinkedAccount, User

from .api_base import PASSWORD, ApiPlaneTestCase

PUBLIC_FIELDS = {'id', 'username', 'full_name', 'profile_image'}
PRIVATE_FIELDS = PUBLIC_FIELDS | {
    'email', 'first_name', 'last_name', 'region', 'date_of_birth', 'date_joined',
    'activity_score', 'activity_scores', 'linked_accounts',
}
# Readable on the administrator plane and nowhere else.
PRIVILEGE_FIELDS = {
    'last_login', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
}
ADMIN_FIELDS = PUBLIC_FIELDS | PRIVILEGE_FIELDS | {
    'email', 'first_name', 'last_name', 'region', 'date_of_birth', 'date_joined',
    'activity_score', 'linked_accounts',
}
# Readable nowhere, on any plane.
CREDENTIAL_FIELDS = {'password', 'auth_token'}


class UserListTests(ApiPlaneTestCase):
    def test_only_administrators_may_read_the_membership_roll(self):
        for caller, expected in (
            (self.as_anonymous, status.HTTP_403_FORBIDDEN),
            (self.as_member, status.HTTP_403_FORBIDDEN),
            (self.as_staff, status.HTTP_403_FORBIDDEN),
            (self.as_admin, status.HTTP_200_OK),
        ):
            with self.subTest(caller=caller.__name__):
                caller()
                self.assertEqual(self.client.get('/api/users/').status_code, expected)

    def test_the_roll_carries_the_administrator_shape(self):
        self.as_admin()

        response = self.client.get('/api/users/')

        self.assertEqual(response.data['count'], 3)
        self.assertEqual(set(response.data['results'][0]), ADMIN_FIELDS)


class UserDetailTests(ApiPlaneTestCase):
    def test_anyone_may_read_one_member_but_only_the_public_shape(self):
        response = self.client.get(f'/api/users/{self.member.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), PUBLIC_FIELDS)

    def test_a_member_reading_someone_else_gets_the_public_shape(self):
        self.as_member()

        response = self.client.get(f'/api/users/{self.staff.pk}/')

        self.assertEqual(set(response.data), PUBLIC_FIELDS)

    def test_a_member_reading_themselves_gets_everything_held_about_them(self):
        self.as_member()

        response = self.client.get(f'/api/users/{self.member.pk}/')

        self.assertEqual(set(response.data), PRIVATE_FIELDS)
        self.assertEqual(response.data['email'], self.member.email)

    def test_an_administrator_reading_someone_else_gets_the_administrator_shape(self):
        self.as_admin()

        response = self.client.get(f'/api/users/{self.member.pk}/')

        self.assertEqual(set(response.data), ADMIN_FIELDS)

    def test_an_administrator_reading_themselves_is_still_a_member(self):
        self.as_admin()

        response = self.client.get(f'/api/users/{self.admin.pk}/')

        self.assertEqual(set(response.data), PRIVATE_FIELDS)

    def test_the_public_shape_carries_no_privilege_flag(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                response = self.client.get(f'/api/users/{self.member.pk}/')
                self.assertEqual(set(response.data) & PRIVILEGE_FIELDS, set())

    def test_a_members_own_shape_carries_no_privilege_flag_either(self):
        self.as_member()

        response = self.client.get('/api/users/me/')

        self.assertEqual(set(response.data) & PRIVILEGE_FIELDS, set())

    def test_the_administrator_shape_carries_every_privilege_flag(self):
        self.as_admin()

        response = self.client.get(f'/api/users/{self.staff.pk}/')

        self.assertTrue(PRIVILEGE_FIELDS <= set(response.data))
        self.assertTrue(response.data['is_staff'])
        self.assertFalse(response.data['is_superuser'])

    def test_no_shape_on_any_plane_carries_a_credential(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff, self.as_admin):
            with self.subTest(caller=caller.__name__):
                caller()
                response = self.client.get(f'/api/users/{self.member.pk}/')
                self.assertEqual(set(response.data) & CREDENTIAL_FIELDS, set())


class OwnRecordTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        ActivityScore.objects.create(user=cls.member, change=5, reason="obecność")
        ActivityScore.objects.create(user=cls.member, change=3, reason="zadanie")
        ActivityScore.objects.create(user=cls.admin, change=99, reason="nie moje")
        LinkedAccount.objects.create(user=cls.member, external_id='123', platform='discord')

    def test_a_member_may_reach_their_own_record_without_knowing_their_id(self):
        self.as_member()

        response = self.client.get('/api/users/me/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(self.member.pk))
        self.assertEqual(set(response.data), PRIVATE_FIELDS)

    def test_anonymous_callers_have_no_own_record(self):
        self.assertEqual(self.client.get('/api/users/me/').status_code, status.HTTP_403_FORBIDDEN)

    def test_the_own_record_is_reachable_through_the_format_suffix_route(self):
        self.as_member()

        response = self.client.get('/api/users/me.json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(self.member.pk))

    def test_the_own_record_carries_the_aggregate_and_the_scores_behind_it(self):
        self.as_member()

        response = self.client.get('/api/users/me/')

        self.assertEqual(response.data['activity_score'], 8)
        self.assertEqual({score['reason'] for score in response.data['activity_scores']},
                         {"obecność", "zadanie"})

    def test_the_own_record_carries_only_ones_own_scores(self):
        self.as_member()

        response = self.client.get('/api/users/me/')

        self.assertNotIn("nie moje", str(response.content))

    def test_the_own_record_carries_ones_linked_accounts(self):
        self.as_member()

        response = self.client.get('/api/users/me/')

        self.assertEqual(response.data['linked_accounts'][0]['platform'], 'discord')

    def test_a_member_with_no_scores_reads_a_zero_rather_than_a_null(self):
        self.client.force_authenticate(self.staff)

        response = self.client.get('/api/users/me/')

        self.assertEqual(response.data['activity_score'], 0)

    def test_reading_a_page_of_members_does_not_aggregate_once_per_row(self):
        for index in range(10):
            user = User.objects.create_user(
                username=f'member{index}', email=f'm{index}@test.com', password=PASSWORD,
            )
            ActivityScore.objects.create(user=user, change=index, reason="test")
        self.as_admin()

        # count, page, then one prefetch each for linked accounts, groups and
        # permissions - three fixed queries, not three per member.
        with self.assertNumQueries(5):
            self.client.get('/api/users/')


class UserWriteTests(ApiPlaneTestCase):
    payload = {
        'username': 'nowy',
        'email': 'nowy@test.com',
        'first_name': 'Nowy',
        'last_name': 'Uzytkownik',
        'region': 'MZ',
        'date_of_birth': '2005-01-01',
    }

    def test_only_administrators_may_create_a_member(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                response = self.client.post('/api/users/', self.payload)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_an_administrator_may_create_a_member(self):
        self.as_admin()

        response = self.client.post('/api/users/', self.payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='nowy').exists())

    def test_an_account_created_here_has_no_usable_password(self):
        self.as_admin()

        self.client.post('/api/users/', self.payload)

        self.assertFalse(User.objects.get(username='nowy').has_usable_password())

    def test_privileges_cannot_be_granted_through_the_api(self):
        self.as_admin()

        self.client.post('/api/users/', {**self.payload, 'is_superuser': True, 'is_staff': True})

        created = User.objects.get(username='nowy')
        self.assertFalse(created.is_superuser)
        self.assertFalse(created.is_staff)

    def test_privileges_are_readable_but_not_writable(self):
        self.as_admin()

        response = self.client.patch(
            f'/api/users/{self.member.pk}/', {'is_superuser': True, 'is_staff': True},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_superuser)
        self.assertFalse(self.member.is_staff)

    def test_a_member_may_not_edit_their_own_record_through_the_api(self):
        self.as_member()

        response = self.client.patch(f'/api/users/{self.member.pk}/', {'first_name': 'Podmieniony'})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_administrators_may_delete_a_member(self):
        self.as_staff()
        self.assertEqual(
            self.client.delete(f'/api/users/{self.member.pk}/').status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.as_admin()
        self.assertEqual(
            self.client.delete(f'/api/users/{self.member.pk}/').status_code,
            status.HTTP_204_NO_CONTENT,
        )

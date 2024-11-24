from datetime import date, time, datetime, timedelta

from rest_framework.test import APITestCase
from rest_framework import status

from accounts.models import User
from seminars.models import Seminar, SeminarGroup


class SeminarViewSetTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass', email='admin@test.com')
        self.regular_user = User.objects.create_user(username='user', password='userpass', email='user@test.com')

        self.group = SeminarGroup.objects.create(name='Test Group')

        self.seminar1 = Seminar.objects.create(
            date=date(2024, 1, 1),
            time=time(10, 0),
            duration=timedelta(hours=1),
            group=self.group,
            difficulty=3,
            theme="Seminar 1",
        )
        self.seminar2 = Seminar.objects.create(
            date=date(2024, 2, 1),
            time=time(14, 0),
            duration=timedelta(hours=2),
            difficulty=2,
            theme="Seminar 2",
        )
        self.seminar3 = Seminar.objects.create(
            date=date(2024, 3, 1),
            time=time(18, 0),
            duration=timedelta(hours=1.5),
            difficulty=2,
            theme="Seminar 3",
        )
        self.seminar2.tutors.set([self.admin_user])

    # Viewing Seminars
    def test_list_seminars(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get('/api/seminars/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_filter_seminars_by_date_range(self):
        self.client.login(username='admin', password='adminpass')
        params = {'start_date': '2024-01-15', 'end_date': '2024-02-20'}
        response = self.client.get('/api/seminars/', query_params=params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['theme'], self.seminar2.theme)

        params = {'start_date': '2024-02-01'}
        response = self.client.get('/api/seminars/', query_params=params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_seminar_by_group(self):
        self.client.login(username='admin', password='adminpass')
        params = {'group': self.group.id}
        response = self.client.get('/api/seminars/', query_params=params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.seminar1.id)

    def test_display_only_param(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get('/api/seminars/', {'display_only': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        seminars = response.data['results']
        for seminar in seminars:
            self.assertTrue('theme' in seminar)
            self.assertTrue('group_name' in seminar)
            self.assertTrue('difficulty_label' in seminar)

            if seminar['theme'] == self.seminar1.theme:
                self.assertEqual(seminar['group_name'], self.group.name)
                self.assertEqual(seminar['difficulty_label'], self.seminar1.difficulty_label)

    def test_retrieve_seminar(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(f'/api/seminars/{self.seminar1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['theme'], self.seminar1.theme)

    # Creating Seminars
    def test_create_seminar(self):
        self.client.login(username='admin', password='adminpass')
        data = {
            "date": "2024-04-01",
            "time": "09:00:00",
            "duration": "01:30:00",
            "theme": "New Seminar",
            "difficulty": 4,
            "group": self.group.id,
        }
        response = self.client.post('/api/seminars/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Seminar.objects.count(), 4)

    # Modifying Seminars
    def test_move_seminar(self):
        self.client.login(username='admin', password='adminpass')
        data = {"date": "2024-04-01"}
        response = self.client.patch(f'/api/seminars/{self.seminar1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.seminar1.refresh_from_db()
        self.assertEqual(self.seminar1.date, datetime.strptime(data['date'], "%Y-%m-%d").date())

    def test_regroup_seminar(self):
        self.client.login(username='admin', password='adminpass')
        data = {"group": self.group.id}
        response = self.client.patch(f'/api/seminars/{self.seminar3.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.seminar3.refresh_from_db()
        self.assertEqual(self.seminar1.group.id, self.group.id)

    def test_swap_tutor_seminar(self):
        self.client.login(username='admin', password='adminpass')
        data = {"tutors": [self.regular_user.id]}
        response = self.client.patch(f'/api/seminars/{self.seminar2.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.seminar2.refresh_from_db()
        self.assertEqual(self.seminar2.tutors.count(), 1)
        self.assertEqual(self.seminar2.tutors.first().username, self.regular_user.username)

    # Deleting Seminars
    def test_delete_seminar(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.delete(f'/api/seminars/{self.seminar3.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Seminar.objects.count(), 2)

    # Permission tests
    def test_regular_user_can_list_seminars(self):
        self.client.login(username='user', password='userpass')
        response = self.client.get('/api/seminars/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anonymous_can_list_seminars(self):
        response = self.client.get('/api/seminars/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_can_retrieve_seminar(self):
        self.client.login(username='user', password='userpass')
        response = self.client.get(f'/api/seminars/{self.seminar1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anonymous_can_retrieve_seminar(self):
        response = self.client.get(f'/api/seminars/{self.seminar1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create_seminar(self):
        self.client.login(username='user', password='userpass')
        data = {
            "date": "2024-04-01",
            "time": "09:00:00",
            "duration": "01:30:00",
            "theme": "New Seminar",
        }
        response = self.client.post('/api/seminars/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Seminar.objects.count(), 3)

    def test_anonymous_cannot_create_seminar(self):
        data = {
            "date": "2024-04-01",
            "time": "09:00:00",
            "duration": "01:30:00",
            "theme": "New Seminar",
        }
        response = self.client.post('/api/seminars/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Seminar.objects.count(), 3)

    def test_regular_user_cannot_modify_seminar(self):
        self.client.login(username='user', password='userpass')
        data = {"date": "2024-04-01"}
        response = self.client.patch(f'/api/seminars/{self.seminar1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_modify_seminar(self):
        data = {"date": "2024-04-01"}
        response = self.client.patch(f'/api/seminars/{self.seminar1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_delete_seminar(self):
        self.client.login(username='user', password='userpass')
        response = self.client.delete(f'/api/seminars/{self.seminar3.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_delete_seminar(self):
        self.client.login(username='user', password='userpass')
        response = self.client.delete(f'/api/seminars/{self.seminar3.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SeminarGroupViewSetTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass', email='admin@test.com')
        self.regular_user = User.objects.create_user(username='user', password='userpass', email='user@test.com')

        self.group1 = SeminarGroup.objects.create(
            name="Group A",
            lead="Lead description for Group A",
            description="Description for Group A",
            discord_role_id="12345",
            default_difficulty=3,
        )
        self.group2 = SeminarGroup.objects.create(
            name="Group B",
            lead="Lead description for Group B",
            description="Description for Group B",
        )

    # Viewing Groups
    def test_list_groups(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get('/api/seminar-groups/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_retrieve_group(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(f'/api/seminar-groups/{self.group1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.group1.name)

    # Creating Groups
    def test_create_group(self):
        self.client.login(username='admin', password='adminpass')
        data = {
            "name": "Group C",
            "lead": "Lead description for Group C",
            "description": "Description for Group C",
            "default_difficulty": 1,
        }
        response = self.client.post('/api/seminar-groups/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SeminarGroup.objects.count(), 3)

    # Modifying Groups
    def test_update_group(self):
        self.client.login(username='admin', password='adminpass')
        data = {"default_difficulty": 2}
        response = self.client.patch(f'/api/seminar-groups/{self.group1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.group1.refresh_from_db()
        self.assertEqual(self.group1.default_difficulty, 2)

    # Deleting Groups
    def test_delete_group(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.delete(f'/api/seminar-groups/{self.group2.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SeminarGroup.objects.count(), 1)

    # Permission tests
    def test_regular_user_can_list_groups(self):
        self.client.login(username='user', password='userpass')
        response = self.client.get('/api/seminar-groups/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_anonymous_can_list_groups(self):
        response = self.client.get('/api/seminar-groups/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_regular_user_can_retrieve_group(self):
        self.client.login(username='user', password='userpass')
        response = self.client.get(f'/api/seminar-groups/{self.group1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anonymous_can_retrieve_group(self):
        response = self.client.get(f'/api/seminar-groups/{self.group1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create_group(self):
        self.client.login(username='user', password='userpass')
        data = {
            "name": "Group C",
            "lead": "Lead description for Group C",
            "description": "Description for Group C",
        }
        response = self.client.post('/api/seminar-groups/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SeminarGroup.objects.count(), 2)

    def test_anonymous_cannot_create_group(self):
        data = {
            "name": "Group C",
            "lead": "Lead description for Group C",
            "description": "Description for Group C",
        }
        response = self.client.post('/api/seminar-groups/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SeminarGroup.objects.count(), 2)

    def test_regular_user_cannot_update_group(self):
        self.client.login(username='user', password='userpass')
        data = {"default_difficulty": 5}
        response = self.client.patch(f'/api/seminar-groups/{self.group1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_update_group(self):
        data = {"default_difficulty": 5}
        response = self.client.patch(f'/api/seminar-groups/{self.group1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_delete_group(self):
        self.client.login(username='user', password='userpass')
        response = self.client.delete(f'/api/seminar-groups/{self.group2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SeminarGroup.objects.count(), 2)

    def test_anonymous_cannot_delete_group(self):
        self.client.login(username='user', password='userpass')
        response = self.client.delete(f'/api/seminar-groups/{self.group2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SeminarGroup.objects.count(), 2)

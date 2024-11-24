from random import seed, randint

from rest_framework.test import APITestCase
from rest_framework import status

from accounts.models import User, ActivityScore


class ActivityScoreViewSetTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass', email='admin@test.com')
        self.regular_user = User.objects.create_user(username='user', password='userpass', email='user@test.com')

        self.score1 = ActivityScore.objects.create(user=self.admin_user, change=10)
        self.score2 = ActivityScore.objects.create(user=self.regular_user, change=20)

    # Viewing Activity Scores
    def test_list_scores(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get('/api/activity-scores/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_retrieve_score(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(f'/api/activity-scores/{self.score1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['change'], self.score1.change)

    # Creating Activity Scores
    def test_create_score(self):
        self.client.login(username='admin', password='adminpass')
        data = {'user': self.regular_user.id, 'change': -5, 'reason': 'no reason'}
        response = self.client.post('/api/activity-scores/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ActivityScore.objects.count(), 3)

    # Deleting Activity Scores
    def test_delete_score(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.delete(f'/api/activity-scores/{self.score1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ActivityScore.objects.count(), 1)

    # Permission Tests
    def test_regular_user_cannot_see_scores(self):
        self.client.login(username='user', password='userpass')
        response = self.client.get('/api/activity-scores/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(f'/api/activity-scores/{self.score1.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_see_scores(self):
        response = self.client.get('/api/activity-scores/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(f'/api/activity-scores/{self.score1.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_create_scores(self):
        self.client.login(username='user', password='userpass')
        data = {'user': self.regular_user.id, 'change': 10}
        response = self.client.post('/api/activity-scores/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_create_scores(self):
        data = {'user': self.regular_user.id, 'change': 10}
        response = self.client.post('/api/activity-scores/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_update_scores(self):
        self.client.login(username='user', password='userpass')
        response = self.client.patch(f'/api/activity-scores/{self.score2.id}/', {'change': 100})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_update_scores(self):
        response = self.client.patch(f'/api/activity-scores/{self.score2.id}/', {'change': 100})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_delete_scores(self):
        self.client.login(username='user', password='userpass')
        response = self.client.delete(f'/api/activity-scores/{self.score2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_delete_scores(self):
        response = self.client.delete(f'/api/activity-scores/{self.score2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserActivityViewSetTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass', email='admin@test.com')

        self.n_users = 10
        self.n_scores = int(3.5 * self.n_users)

        seed(42)
        self.users = User.objects.bulk_create(
            [User(username=f'user{i}', password='userpass', email=f'user{i}@test.com') for i in range(self.n_users)]
        )
        self.scores = ActivityScore.objects.bulk_create(
            [ActivityScore(user=self.users[i % self.n_users], change=randint(-10, 100)) for i in range(self.n_scores)]
        )

    def test_list_top_scores(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get('/api/user-activity/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], self.n_users)

        # test score_calculation
        manual_scores = {user.id: sum(score.change for score in self.scores if score.user == user)
                         for user in self.users}
        for user in response.data['results']:
            self.assertEqual(user['total_score'], manual_scores[user['id']])

        # test decreasing ordering by score
        scores = [user['total_score'] for user in response.data['results']]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_retrieve_user_score(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(f'/api/user-activity/{self.users[0].id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # test score_calculation
        manual_score = sum(score.change for score in self.scores if score.user == self.users[0])
        self.assertEqual(response.data['total_score'], manual_score)

        # test default score
        dummy_user = User.objects.create_user(username='dummy', password='dummypass', email='dummy@test.com')
        response = self.client.get(f'/api/user-activity/{dummy_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_score'], 0)

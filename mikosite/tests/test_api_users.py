from rest_framework.test import APITestCase
from rest_framework import status

from accounts.models import User, LinkedAccount


class UserViewSetTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass', email='admin@test.com')
        self.user1 = User.objects.create_user(username='user1', password='userpass', email='user1@test.com')
        self.user2 = User.objects.create_user(username='user2', password='userpass', email='user2@test.com')

    # Viewing Users
    def test_list_users(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_retrieve_user(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(f'/api/users/{self.user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user1.username)

        # test if correct serializer is used
        for field in ['email', 'surname', 'region', 'linked_accounts']:
            self.assertTrue(field in response.data)

    # Permission tests
    def test_regular_user_cannot_list_users(self):
        self.client.login(username='user1', password='userpass')
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_list_users(self):
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_can_retrieve_user(self):
        self.client.login(username='user1', password='userpass')
        response = self.client.get(f'/api/users/{self.user2.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # test if correct serializer is used
        for field in ['email', 'surname', 'region', 'linked_accounts']:
            self.assertFalse(field in response.data)

    def test_anonymous_can_retrieve_user(self):
        response = self.client.get(f'/api/users/{self.user2.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # test if correct serializer is used
        for field in ['email', 'surname', 'region', 'linked_accounts']:
            self.assertFalse(field in response.data)

    def test_regular_user_cannot_create_user(self):
        self.client.login(username='user1', password='userpass')
        response = self.client.post('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_create_user(self):
        response = self.client.post('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_modify_user(self):
        self.client.login(username='user1', password='userpass')
        response = self.client.patch(f'/api/users/{self.user2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_modify_user(self):
        response = self.client.patch(f'/api/users/{self.user2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_delete_user(self):
        self.client.login(username='user1', password='userpass')
        response = self.client.delete(f'/api/users/{self.user2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_delete_user(self):
        response = self.client.delete(f'/api/users/{self.user2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class LinkedAccountViewSetTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass', email='admin@test.com')
        self.regular_user = User.objects.create_user(username='user', password='userpass', email='user@test.com')

        self.user_discord = LinkedAccount.objects.create(external_id='123', platform='discord', user=self.regular_user)
        self.user_yt = LinkedAccount.objects.create(external_id='456', platform='yt', user=self.regular_user)

        self.admin_discord = LinkedAccount.objects.create(external_id='789', platform='discord', user=self.admin_user)

    # Viewing LinkedAccounts
    def test_list_linked_accounts(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get('/api/linked-accounts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_retrieve_linked_account(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(f'/api/linked-accounts/{self.user_discord.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['external_id'], '123')

        response = self.client.get(f'/api/users/{self.regular_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['linked_accounts']), self.regular_user.linked_accounts.count())

    # Creating LinkedAccounts
    def test_create_linked_account(self):
        self.client.login(username='admin', password='adminpass')
        data = {
            'external_id': '555',
            'platform': 'yt',
            'user': self.admin_user.id,
        }
        response = self.client.post('/api/linked-accounts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LinkedAccount.objects.count(), 4)

        response = self.client.get(f'/api/users/{self.admin_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['linked_accounts']), 2)

    def test_linked_account_unique_constraints(self):
        self.client.login(username='admin', password='adminpass')

        # external_id repeated but with different platform
        allowed_case = {
            'external_id': '123',
            'platform': 'fb',
            'user': self.regular_user.id,
        }
        response = self.client.post('/api/linked-accounts/', allowed_case)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        fail_cases = [
            {  # external_id repeated with same platform (different user)
                'external_id': '123',
                'platform': 'discord',
                'user': self.admin_user.id,
            },
            {  # platform repeated for the same user
                'external_id': '111',
                'platform': 'yt',
                'user': self.regular_user.id,
            }
        ]
        for allowed_case in fail_cases:
            response = self.client.post('/api/linked-accounts/', allowed_case)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Modifying LinkedAccounts
    def test_modify_linked_account(self):
        self.client.login(username='admin', password='adminpass')
        data = {'external_id': '555'}
        response = self.client.patch(f'/api/linked-accounts/{self.user_discord.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_discord.refresh_from_db()
        self.assertEqual(self.user_discord.external_id, '555')

    # Deleting LinkedAccounts
    def test_delete_linked_account(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.delete(f'/api/linked-accounts/{self.user_discord.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(LinkedAccount.objects.count(), 2)

    # Permission tests
    def test_regular_user_cannot_see_linked_accounts(self):
        self.client.login(username='user', password='userpass')
        response = self.client.get('/api/linked-accounts/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(f'/api/linked-accounts/{self.user_discord.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_see_linked_accounts(self):
        response = self.client.get('/api/linked-accounts/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(f'/api/linked-accounts/{self.user_discord.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_create_linked_account(self):
        self.client.login(username='user', password='userpass')
        data = {
            'external_id': '555',
            'platform': 'fb',
            'user': self.regular_user.id,
        }
        response = self.client.post('/api/linked-accounts/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(LinkedAccount.objects.count(), 3)

    def test_anonymous_cannot_create_linked_account(self):
        data = {
            'external_id': '555',
            'platform': 'fb',
            'user': self.regular_user.id,
        }
        response = self.client.post('/api/linked-accounts/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(LinkedAccount.objects.count(), 3)

    def test_regular_user_cannot_modify_linked_account(self):
        self.client.login(username='user', password='userpass')
        data = {'external_id': '555'}
        response = self.client.patch(f'/api/linked-accounts/{self.user_discord.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_modify_linked_account(self):
        data = {'external_id': '555'}
        response = self.client.patch(f'/api/linked-accounts/{self.user_discord.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_delete_linked_account(self):
        self.client.login(username='user', password='userpass')
        response = self.client.delete(f'/api/linked-accounts/{self.user_discord.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_delete_linked_account(self):
        response = self.client.delete(f'/api/linked-accounts/{self.user_discord.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

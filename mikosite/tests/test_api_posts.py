from datetime import date, time, datetime

from rest_framework.test import APITestCase
from rest_framework import status

from accounts.models import User
from mainSite.models import Post, Image


class PostViewSetTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass', email='admin@test.com')
        self.regular_user = User.objects.create_user(username='user', password='userpass', email='user@test.com')

        self.image = Image.objects.create(image='/path/to/image.jpg')

        self.post1 = Post.objects.create(
            title="Post 1",
            date = date(2024, 1, 1),
            time = time(18, 0),
            text_field_1="Post content.",
        )
        self.post2 = Post.objects.create(
            title="Post 2",
            date = date(2024, 2, 1),
            time = time(17, 0),
        )
        self.post3 = Post.objects.create(
            title="Post 3",
            date = date(2024, 3, 1),
            time = time(16, 0),
        )
        self.post1.authors.set([self.admin_user])
        self.post2.authors.set([self.regular_user])
        self.post3.authors.set([self.admin_user])
        self.post1.images.set([self.image])

    # Viewing Posts
    def test_list_posts(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_filter_posts_by_date_range(self):
        self.client.login(username='admin', password='adminpass')
        params = {'start_date': '2024-01-15', 'end_date': '2024-02-20'}
        response = self.client.get('/api/posts/', query_params=params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], self.post2.title)

        params = {'start_date': '2024-02-01'}
        response = self.client.get('/api/posts/', query_params=params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_display_only_param(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get('/api/posts/', {'display_only': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        posts = response.data['results']
        for post in posts:
            self.assertTrue('title' in post)
            self.assertTrue('authors' in post)

            if post['id'] == self.post1.id:
                self.assertTrue(isinstance(post['authors'][0], str))
                self.assertNotEqual(post['authors'][0], self.admin_user.id)
                self.assertEqual(post['authors'][0], self.admin_user.full_name)

    def test_retrieve_post(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(f'/api/posts/{self.post1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.post1.title)

    # Creating Posts
    def test_create_post(self):
        self.client.login(username='admin', password='adminpass')
        data = {
            "title": "Test Post",
            "date": "2024-04-01",
            "time": "18:00:00",
            "authors": [self.admin_user.id],
        }
        response = self.client.post('/api/posts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 4)

    # Modifying Posts
    def test_modify_date_post(self):
        self.client.login(username='admin', password='adminpass')
        data = {"date": "2024-04-01"}
        response = self.client.patch(f'/api/posts/{self.post1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.date, datetime.strptime(data['date'], "%Y-%m-%d").date())

    def test_swap_image_post(self):
        self.client.login(username='admin', password='adminpass')
        new_image = Image.objects.create(image='/path/to/other/image.jpg')
        data = {"images": [new_image.id]}
        response = self.client.patch(f'/api/posts/{self.post1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.images.count(), 1)
        self.assertEqual(self.post1.images.first().image, new_image.image)

    # Deleting Posts
    def test_delete_post(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.delete(f'/api/posts/{self.post3.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 2)

    # Permission tests
    def test_regular_user_can_list_posts(self):
        self.client.login(username='user', password='userpass')
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anonymous_can_list_posts(self):
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_can_retrieve_post(self):
        self.client.login(username='user', password='userpass')
        response = self.client.get(f'/api/posts/{self.post1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anonymous_can_retrieve_post(self):
        response = self.client.get(f'/api/posts/{self.post1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create_post(self):
        self.client.login(username='user', password='userpass')
        data = {
            "title": "Forbidden Post",
            "date": "2024-04-01",
            "time": "18:00:00",
            "authors": [self.regular_user.id],
        }
        response = self.client.post('/api/posts/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Post.objects.count(), 3)

    def test_anonymous_cannot_create_post(self):
        data = {
            "title": "Forbidden Post",
            "date": "2024-04-01",
            "time": "18:00:00",
            "authors": [self.regular_user.id],
        }
        response = self.client.post('/api/posts/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Post.objects.count(), 3)

    def test_regular_user_cannot_modify_post(self):
        self.client.login(username='user', password='userpass')
        data = {"date": "2024-04-01"}
        response = self.client.patch(f'/api/posts/{self.post1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_modify_post(self):
        data = {"date": "2024-04-01"}
        response = self.client.patch(f'/api/posts/{self.post1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_delete_post(self):
        self.client.login(username='user', password='userpass')
        response = self.client.delete(f'/api/posts/{self.post3.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_delete_post(self):
        self.client.login(username='user', password='userpass')
        response = self.client.delete(f'/api/posts/{self.post3.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PostImageViewSetTests(APITestCase):
    pass

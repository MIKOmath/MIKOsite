"""Announcements and the images they embed."""
from datetime import date, time

from rest_framework import status

from mainSite.models import Image, Post

from .api_base import ApiPlaneTestCase

PUBLIC_POST_FIELDS = {
    'id', 'title', 'subtitle', 'date', 'time', 'content', 'authors', 'file', 'images',
}
PUBLIC_AUTHOR_FIELDS = {'id', 'username', 'full_name', 'profile_image'}


class PostReadTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.image = Image.objects.create(image='post_images/i.webp')
        cls.post = Post.objects.create(
            title="Ogłoszenie", subtitle="Podtytuł", date=date(2026, 3, 1),
            time=time(12, 0), content="Treść",
        )
        cls.post.authors.set([cls.member])
        cls.post.images.set([cls.image])

    def test_anyone_may_read_announcements(self):
        response = self.client.get('/api/posts/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data['results'][0]), PUBLIC_POST_FIELDS)

    def test_authors_come_back_as_public_profiles(self):
        response = self.client.get(f'/api/posts/{self.post.pk}/')

        self.assertEqual(set(response.data['authors'][0]), PUBLIC_AUTHOR_FIELDS)
        self.assertEqual(response.data['authors'][0]['full_name'], self.member.full_name)

    def test_an_author_profile_carries_nothing_private(self):
        response = self.client.get(f'/api/posts/{self.post.pk}/')

        self.assertNotIn(self.member.email, str(response.content))

    def test_embedded_images_come_back_resolved(self):
        response = self.client.get(f'/api/posts/{self.post.pk}/')

        self.assertEqual(response.data['images'][0]['id'], self.image.pk)
        self.assertIn('i.webp', response.data['images'][0]['image'])

    def test_the_old_display_only_switch_is_gone_and_harmless(self):
        plain = self.client.get(f'/api/posts/{self.post.pk}/').data
        legacy = self.client.get(f'/api/posts/{self.post.pk}/', {'display_only': '1'}).data

        self.assertEqual(plain, legacy)

    def test_the_administrator_shape_is_writable_and_uses_ids(self):
        self.as_admin()

        response = self.client.get(f'/api/posts/{self.post.pk}/')

        self.assertEqual(response.data['authors'], [self.member.pk])
        self.assertEqual(response.data['images'], [self.image.pk])

    def test_announcements_come_back_newest_first(self):
        Post.objects.create(title="Nowsze", date=date(2026, 4, 1), time=time(12, 0))

        titles = [item['title'] for item in self.client.get('/api/posts/').data['results']]

        self.assertEqual(titles, ["Nowsze", "Ogłoszenie"])

    def test_authors_and_images_are_joined_rather_than_fetched_per_row(self):
        for index in range(10):
            post = Post.objects.create(title=f"Post {index}", date=date(2026, 3, 2), time=time(12, 0))
            post.authors.set([self.member])
            post.images.set([self.image])

        with self.assertNumQueries(4):  # count, page, prefetched authors, prefetched images
            self.client.get('/api/posts/')


class PostFilterTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Post.objects.create(title="Marzec", date=date(2026, 3, 1), time=time(12, 0))
        Post.objects.create(title="Kwiecień", date=date(2026, 4, 1), time=time(12, 0))

    def titles(self, params):
        return [item['title'] for item in self.client.get('/api/posts/', params).data['results']]

    def test_the_date_window_filters_both_ends(self):
        self.assertEqual(self.titles({'start_date': '2026-03-15'}), ["Kwiecień"])
        self.assertEqual(self.titles({'end_date': '2026-03-15'}), ["Marzec"])

    def test_an_unknown_query_parameter_is_ignored_rather_than_obeyed(self):
        self.assertEqual(len(self.titles({'nonsense': 'x'})), 2)


class PostWriteTests(ApiPlaneTestCase):
    def payload(self):
        return {
            'title': "Nowy",
            'date': '2026-05-01',
            'time': '12:00',
            'authors': [str(self.member.pk)],
        }

    def test_writing_is_refused_off_the_administrator_plane(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                self.assertEqual(
                    self.client.post('/api/posts/', self.payload()).status_code,
                    status.HTTP_403_FORBIDDEN,
                )

    def test_an_administrator_may_publish(self):
        self.as_admin()

        response = self.client.post('/api/posts/', self.payload())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Post.objects.filter(title="Nowy").exists())


class PostImageTests(ApiPlaneTestCase):
    """Images have no endpoint; they travel with the announcements."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.image = Image.objects.create(image='post_images/i.webp')
        cls.post = Post.objects.create(
            title="Ogloszenie", date=date(2026, 3, 1), time=time(12, 0),
        )
        cls.post.images.set([cls.image])

    def test_the_image_library_is_not_routed_at_all(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff, self.as_admin):
            with self.subTest(caller=caller.__name__):
                caller()
                self.assertEqual(
                    self.client.get('/api/post-images/').status_code, status.HTTP_404_NOT_FOUND,
                )

    def test_an_image_still_reaches_the_public_through_its_post(self):
        response = self.client.get(f'/api/posts/{self.post.pk}/')

        self.assertEqual(response.data['images'][0]['id'], self.image.pk)

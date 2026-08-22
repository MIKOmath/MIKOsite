"""Team cards and the badges they share, over the two access planes."""
import tempfile

from django.test import override_settings
from rest_framework import status

from mainSite.models import Badge, Bio

from .api_base import ApiPlaneTestCase, tiny_image
from .bio_base import TEST_ORDER, make_person

PUBLIC_BIO_FIELDS = {'id', 'name', 'user', 'description', 'image_url', 'badges'}
ADMIN_BIO_FIELDS = {'id', 'user', 'description', 'image', 'badges', 'order', 'is_published'}

PUBLIC_BADGE_FIELDS = {'id', 'text', 'color', 'icon'}
ADMIN_BADGE_FIELDS = PUBLIC_BADGE_FIELDS | {'order'}


class BioReadTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.shown = Bio.objects.create(
            user=make_person('widoczny1', "Widoczny", "Cztery"),
            description="Widać.",
            order=TEST_ORDER,
        )
        cls.hidden = Bio.objects.create(
            user=make_person('ukryty11', "Ukryty", "Cztery"),
            description="Nie widać.",
            order=TEST_ORDER + 1,
            is_published=False,
        )

    def test_anyone_may_read_the_cards(self):
        response = self.client.get('/api/bios/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data['results'][0]), PUBLIC_BIO_FIELDS)

    def test_a_card_carries_the_name_off_its_account(self):
        response = self.client.get(f'/api/bios/{self.shown.pk}/')

        self.assertEqual(response.data['name'], "Widoczny Cztery")

    def test_an_unpublished_card_is_invisible_off_the_administrator_plane(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                names = [item['name'] for item in self.client.get('/api/bios/').data['results']]
                self.assertIn("Widoczny Cztery", names)
                self.assertNotIn("Ukryty Cztery", names)

    def test_an_unpublished_card_is_not_reachable_by_id_either(self):
        self.as_member()

        response = self.client.get(f'/api/bios/{self.hidden.pk}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_an_administrator_sees_both_and_the_switch(self):
        self.as_admin()

        response = self.client.get('/api/bios/')

        self.assertEqual(response.data['count'], Bio.objects.count())
        self.assertEqual(set(response.data['results'][0]), ADMIN_BIO_FIELDS)

    def test_cards_come_back_in_their_display_order(self):
        Bio.objects.create(
            user=make_person('pierwszy1', "Pierwszy", "Zawsze"),
            description="Na początku.",
            order=0,
        )

        names = [item['name'] for item in self.client.get('/api/bios/?limit=100').data['results']]

        self.assertLess(names.index("Pierwszy Zawsze"), names.index("Widoczny Cztery"))

    def test_a_card_lists_its_badges_in_the_global_order(self):
        early = Badge.objects.create(text="Wcześniej", order=1)
        late = Badge.objects.create(text="Później", order=2)
        self.shown.badges.set([late, early])

        response = self.client.get(f'/api/bios/{self.shown.pk}/')

        self.assertEqual([badge['text'] for badge in response.data['badges']],
                         ["Wcześniej", "Później"])
        self.assertEqual(set(response.data['badges'][0]), PUBLIC_BADGE_FIELDS)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class BioWriteTests(ApiPlaneTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.subject = make_person('opisany1', "Opisany", "Ktos")

    def payload(self, **overrides):
        data = {'user': str(self.subject.pk), 'description': "Nowy opis.", 'order': TEST_ORDER}
        data.update(overrides)
        return data

    def test_writing_is_refused_off_the_administrator_plane(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                response = self.client.post('/api/bios/', self.payload())
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_an_administrator_may_add_and_then_hide_a_card(self):
        self.as_admin()

        created = self.client.post('/api/bios/', self.payload())
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        hidden = self.client.patch(f"/api/bios/{created.data['id']}/", {'is_published': False})
        self.assertEqual(hidden.status_code, status.HTTP_200_OK)

        self.as_anonymous()
        names = [item['name'] for item in self.client.get('/api/bios/?limit=100').data['results']]
        self.assertNotIn("Opisany Ktos", names)

    def test_a_photo_posted_over_the_api_gets_the_same_treatment_as_an_upload(self):
        self.as_admin()

        created = self.client.post('/api/bios/', self.payload(image=tiny_image()))

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Bio.objects.get(pk=created.data['id']).image.name.endswith('.webp'))

    def test_badges_may_be_pinned_on_over_the_api(self):
        self.as_admin()
        badge = Badge.objects.create(text="Nowa", order=1)

        created = self.client.post('/api/bios/', self.payload(badges=[badge.pk]))

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(list(Bio.objects.get(pk=created.data['id']).badges.all()), [badge])

    def test_a_new_card_is_published_whichever_way_it_was_posted(self):
        """An HTML form omits an unticked checkbox, which DRF reads as False."""
        self.as_admin()

        for transport in ('multipart', 'json'):
            with self.subTest(transport=transport):
                person = make_person(f'trans-{transport}'[:20], "Nowy", transport.title())
                created = self.client.post(
                    '/api/bios/', self.payload(user=str(person.pk)), format=transport,
                )
                self.assertEqual(created.status_code, status.HTTP_201_CREATED)
                self.assertTrue(created.data['is_published'])

    def test_one_account_carries_at_most_one_card(self):
        self.as_admin()
        self.client.post('/api/bios/', self.payload())

        second = self.client.post('/api/bios/', self.payload(description="Drugi."))

        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_a_nameless_account_may_not_be_published_over_the_api_either(self):
        """The model's own rule, reached through ModelCleanMixin."""
        self.as_admin()
        nameless = make_person('bezimien', first_name='', last_name='')

        refused = self.client.post('/api/bios/', self.payload(user=str(nameless.pk)))

        self.assertEqual(refused.status_code, status.HTTP_400_BAD_REQUEST)


class BadgeReadTests(ApiPlaneTestCase):
    def test_anyone_may_read_the_badges(self):
        response = self.client.get('/api/badges/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data['results'][0]), PUBLIC_BADGE_FIELDS)

    def test_an_administrator_sees_the_lever_the_public_does_not(self):
        self.as_admin()

        response = self.client.get('/api/badges/')

        self.assertEqual(set(response.data['results'][0]), ADMIN_BADGE_FIELDS)


class BadgeWriteTests(ApiPlaneTestCase):
    def test_writing_is_refused_off_the_administrator_plane(self):
        for caller in (self.as_anonymous, self.as_member, self.as_staff):
            with self.subTest(caller=caller.__name__):
                caller()
                response = self.client.post('/api/badges/', {'text': "Nowa", 'color': 'normal'})
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_a_badge_added_without_an_icon_gets_its_colour_default(self):
        self.as_admin()

        for colour in Badge.Color:
            with self.subTest(colour=colour):
                created = self.client.post(
                    '/api/badges/', {'text': f"Nowa {colour}", 'color': colour},
                )
                self.assertEqual(created.status_code, status.HTTP_201_CREATED)
                self.assertEqual(created.data['icon'], Badge.STYLES[colour].icon)

    def test_an_icon_that_was_asked_for_survives(self):
        self.as_admin()

        created = self.client.post(
            '/api/badges/', {'text': "Grafik", 'color': 'normal', 'icon': 'palette'},
        )

        self.assertEqual(created.data['icon'], 'palette')

    def test_two_badges_may_not_share_a_caption(self):
        self.as_admin()
        self.client.post('/api/badges/', {'text': "Jedyna", 'color': 'normal'})

        second = self.client.post('/api/badges/', {'text': "Jedyna", 'color': 'award'})

        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

"""The about page's team cards, and the name lock that comes with them."""
import tempfile

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from PIL import Image as PILImage

from accounts.models import User
from mainSite.models import BIO_IMAGE_SIZE, Badge, Bio

from .auth_base import PASSWORD
from .bio_base import (
    ABOUT_URL,
    BIOS_CACHE_KEY,
    FIXED_CARD_NAME,
    PROFILE_URL,
    TEST_ORDER,
    card_names,
    make_bio,
    make_person,
    photo,
)


class BadgeTests(TestCase):
    def test_a_new_badge_wears_the_icon_its_colour_defaults_to(self):
        for colour in Badge.Color:
            with self.subTest(colour=colour):
                badge = Badge.objects.create(text=f"Plakietka {colour}", color=colour)
                self.assertEqual(badge.icon, Badge.STYLES[colour].icon)

    def test_an_icon_that_was_asked_for_survives_the_default(self):
        badge = Badge.objects.create(text="Grafik", color=Badge.Color.NORMAL, icon='palette')

        self.assertEqual(badge.icon, 'palette')

    def test_clearing_the_icon_hands_the_colour_default_back(self):
        badge = Badge.objects.create(text="Grafik", color=Badge.Color.NORMAL, icon='palette')

        badge.icon = ''
        badge.save()

        self.assertEqual(badge.icon, 'co_present')

class BioPageTests(TestCase):
    def setUp(self):
        # The cards are cached, and a locmem cache outlives a test.
        cache.clear()

    def test_a_card_reads_its_name_off_the_account_it_is_linked_to(self):
        make_bio('nowak1')

        self.assertIn("Marek Testowy", card_names(self.client.get(ABOUT_URL)))

    def test_renaming_the_account_renames_the_card(self):
        bio = make_bio('nowak2')
        self.assertIn("Marek Testowy", card_names(self.client.get(ABOUT_URL)))

        bio.user.first_name = "Marysia"
        bio.user.save()

        self.assertIn("Marysia Testowy", card_names(self.client.get(ABOUT_URL)))

    def test_signing_in_does_not_throw_the_page_away(self):
        """Only `last_login` moves, so the cards have to survive it."""
        make_bio('nowak3')
        self.client.get(ABOUT_URL)
        cached = cache.get(BIOS_CACHE_KEY)
        self.assertIsNotNone(cached)

        self.client.login(username='nowak3', password=PASSWORD)

        self.assertEqual(cache.get(BIOS_CACHE_KEY), cached)

    def test_an_unpublished_card_is_off_the_page(self):
        make_bio('nowak4', is_published=False)

        self.assertNotIn("Marek Testowy", card_names(self.client.get(ABOUT_URL)))

    def test_publishing_a_card_puts_it_back_on_the_page(self):
        bio = make_bio('nowak5', is_published=False)
        self.client.get(ABOUT_URL)

        bio.is_published = True
        bio.save()

        self.assertIn("Marek Testowy", card_names(self.client.get(ABOUT_URL)))

    def test_the_cards_come_in_the_order_they_were_given(self):
        make_bio('drugi1', order=TEST_ORDER + 1, first_name="Drugi", last_name="Zawsze")
        make_bio('pierw1', order=TEST_ORDER, first_name="Pierwszy", last_name="Zawsze")

        names = card_names(self.client.get(ABOUT_URL))

        self.assertLess(names.index("Pierwszy Zawsze"), names.index("Drugi Zawsze"))

    def test_badges_line_up_globally_not_in_the_order_they_were_pinned_on(self):
        early = Badge.objects.create(text="Wcześniej", order=1)
        late = Badge.objects.create(text="Później", order=2)
        bio = make_bio('nowak6', badges=[late, early])

        self.assertEqual(
            [badge['text'] for badge in bio.display_dict()['badges']],
            ["Wcześniej", "Później"],
        )

    def test_moving_a_badge_moves_it_on_every_card_at_once(self):
        early = Badge.objects.create(text="Wcześniej", order=1)
        late = Badge.objects.create(text="Później", order=2)
        cards = [make_bio('nowak7', badges=[early, late]), make_bio('nowak8', badges=[early, late])]

        late.order = 0
        late.save()

        for bio in cards:
            with self.subTest(bio=bio.user.username):
                bio.refresh_from_db()
                self.assertEqual(
                    [badge['text'] for badge in bio.display_dict()['badges']],
                    ["Później", "Wcześniej"],
                )

    def test_the_thank_you_card_stays_on_the_page_with_nothing_stored(self):
        Bio.objects.all().delete()

        self.assertEqual(card_names(self.client.get(ABOUT_URL)), [FIXED_CARD_NAME])

    def test_a_card_without_a_photo_falls_back_to_the_icon(self):
        Bio.objects.all().delete()
        make_bio('nowak9')

        response = self.client.get(ABOUT_URL)

        # Its own, and the thank-you card's.
        self.assertContains(response, 'photo-placeholder--icon', count=2)

    def test_a_card_may_not_be_published_over_a_nameless_account(self):
        bio = Bio(user=make_person('bezimie', first_name='', last_name=''), description="x")

        with self.assertRaises(ValidationError):
            bio.full_clean()

    def test_a_nameless_account_may_still_carry_a_draft(self):
        bio = Bio(
            user=make_person('bezimi2', first_name='', last_name=''),
            description="x",
            is_published=False,
        )

        bio.full_clean()


class MigratedCardTests(TestCase):
    """What the data migration carried over is what the page used to say."""

    def setUp(self):
        cache.clear()

    def test_every_hand_written_card_arrived(self):
        names = card_names(self.client.get(ABOUT_URL))

        self.assertEqual(len(names), 13)
        self.assertEqual(names[0], "Filip Manijak")
        self.assertEqual(names[-1], FIXED_CARD_NAME)

    def test_the_placeholders_cannot_be_signed_in_to(self):
        placeholders = User.objects.filter(username__startswith='bio-')

        self.assertEqual(placeholders.count(), 12)
        for user in placeholders:
            with self.subTest(user=user.username):
                self.assertFalse(user.is_active)
                self.assertFalse(user.has_usable_password())

    def test_the_descriptions_kept_their_non_breaking_spaces(self):
        bio = Bio.objects.get(user__username='bio-filip-manijak')

        self.assertIn('\u00a0', bio.description)

    def test_a_card_photo_arrived_at_the_size_an_upload_would_have(self):
        bio = Bio.objects.get(user__username='bio-filip-manijak')

        with PILImage.open(bio.image.path) as stored:
            self.assertEqual(stored.size, BIO_IMAGE_SIZE)
            self.assertEqual(stored.format, 'WEBP')

    def test_the_badge_order_runs_roles_subjects_then_what_was_won(self):
        order = {badge.text: badge.order for badge in Badge.objects.all()}

        self.assertLess(order["CEO"], order["Matematyka"])
        self.assertLess(order["Matematyka"], order["IMO Gold"])
        self.assertLess(order["IMO Gold"], order["Laureat OI"])
        self.assertLess(order["Laureat OI"], order["Laureat OAI"])
        self.assertLess(order["Laureat OAI"], order["Finalista OM"])


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class BioImageTests(TestCase):
    def test_an_upload_is_cropped_to_the_card_and_stored_as_webp(self):
        bio = Bio.objects.create(user=make_person('foto11'), description="x", image=photo())

        with PILImage.open(bio.image.path) as stored:
            self.assertEqual(stored.size, BIO_IMAGE_SIZE)
            self.assertEqual(stored.format, 'WEBP')
        self.assertTrue(bio.image.name.endswith('.webp'))

    def test_a_replacement_takes_the_old_file_with_it(self):
        bio = Bio.objects.create(user=make_person('foto14'), description="x", image=photo())
        first = bio.image.name

        bio.image = photo(name='another.png')
        bio.save()

        self.assertNotEqual(bio.image.name, first)
        self.assertFalse(bio.image.storage.exists(first))

    def test_clearing_the_photo_takes_the_file_with_it(self):
        bio = Bio.objects.create(user=make_person('foto16'), description="x", image=photo())
        stored = bio.image.name

        bio.image = None
        bio.save()

        self.assertFalse(bio.image.storage.exists(stored))

    def test_saving_again_leaves_the_photo_alone(self):
        bio = Bio.objects.create(user=make_person('foto15'), description="x", image=photo())
        stored = bio.image.name

        bio.description = "y"
        bio.save()

        self.assertEqual(bio.image.name, stored)
        self.assertTrue(bio.image.storage.exists(stored))

    def test_a_profile_picture_goes_through_the_same_mill(self):
        """Both models share one conversion, so they must not drift apart."""
        person = make_person('foto17')

        person.profile_image = photo()
        person.save()

        with PILImage.open(person.profile_image.path) as stored:
            self.assertEqual(stored.size, User.IMAGE_SIZE)
            self.assertEqual(stored.format, 'WEBP')


class ProfileNameLockTests(TestCase):
    """A name on a published card is the card, so respelling it takes the right."""

    LOCK_NOTE = "Administrator ograniczył możliwość zmiany imienia i nazwiska dla tego konta."

    def setUp(self):
        cache.clear()
        self.user = make_person('profil1')
        self.card = Bio.objects.create(user=self.user, description="Opis.", order=TEST_ORDER)
        self.client.force_login(self.user)

    def payload(self, **overrides):
        data = {
            'first_name': "Podszywacz",
            'last_name': "Falszywy",
            'region': 'MZ',
            'date_of_birth': '2000-01-01',
        }
        data.update(overrides)
        return data

    def allow_editing_cards(self):
        self.user.user_permissions.add(Permission.objects.get(codename='change_bio'))
        # The permission cache rides on the instance the session will hand back.
        self.user = User.objects.get(pk=self.user.pk)
        self.client.force_login(self.user)

    def test_the_name_is_sent_read_only_and_says_why(self):
        response = self.client.get(PROFILE_URL)

        self.assertContains(response, 'name="first_name"')
        self.assertContains(response, 'name-locked-hint')
        self.assertContains(response, self.LOCK_NOTE)

    def test_the_name_opens_up_to_somebody_who_may_edit_cards(self):
        self.allow_editing_cards()

        response = self.client.get(PROFILE_URL)

        self.assertContains(response, 'name="first_name"')
        self.assertNotContains(response, 'name-locked-hint')

    def test_a_member_with_no_card_names_themselves(self):
        self.card.delete()

        self.assertNotContains(self.client.get(PROFILE_URL), 'name-locked-hint')
        self.client.post(PROFILE_URL, self.payload())

        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Podszywacz Falszywy")

    def test_a_card_the_page_does_not_show_does_not_freeze_the_name(self):
        self.card.is_published = False
        self.card.save()

        self.assertNotContains(self.client.get(PROFILE_URL), 'name-locked-hint')
        self.client.post(PROFILE_URL, self.payload())

        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Podszywacz Falszywy")

    def test_a_posted_name_is_ignored_without_the_right(self):
        self.client.post(PROFILE_URL, self.payload())

        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Marek Testowy")

    def test_the_rest_of_the_profile_still_saves_without_the_right(self):
        response = self.client.post(PROFILE_URL, self.payload(region='MA'))

        self.assertContains(response, "zaktualizowany")
        self.user.refresh_from_db()
        self.assertEqual(self.user.region, 'MA')

    def test_a_posted_name_lands_with_the_right(self):
        self.allow_editing_cards()

        self.client.post(PROFILE_URL, self.payload())

        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Podszywacz Falszywy")

    def test_the_card_holds_still_when_the_name_behind_it_is_refused(self):
        self.client.post(PROFILE_URL, self.payload())

        self.assertIn("Marek Testowy", card_names(self.client.get(ABOUT_URL)))

    def test_signup_still_asks_everyone_for_a_name(self):
        """The lock rides on the profile form; the signup form shares the row."""
        self.client.logout()

        response = self.client.get('/accounts/signup/')

        self.assertContains(response, 'name="first_name"')
        self.assertNotContains(response, 'name-locked-hint')


class BioAdminTests(TestCase):
    """The changelist edits two fields, so a rule about a third must not 500."""

    def setUp(self):
        boss = User.objects.create_superuser(
            username='szefowa', email='szefowa@test.invalid', password=PASSWORD,
        )
        self.client.force_login(boss)
        self.card = Bio.objects.create(
            user=make_person('bezimi3', first_name='', last_name=''),
            description="x",
            order=TEST_ORDER,
            is_published=False,
        )

    def test_publishing_a_nameless_card_from_the_list_is_a_form_error(self):
        response = self.client.post('/admin/mainSite/bio/', {
            'action': '',
            '_save': 'Zapisz',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-id': str(self.card.pk),
            'form-0-order': str(TEST_ORDER),
            'form-0-is_published': 'on',
        })

        self.assertEqual(response.status_code, 200)
        self.card.refresh_from_db()
        self.assertFalse(self.card.is_published)

    def test_the_badges_sit_next_to_the_cards_in_the_index(self):
        page = self.client.get('/admin/').content.decode()

        self.assertLess(page.index('/admin/mainSite/bio/'), page.index('/admin/mainSite/badge/'))
        self.assertNotIn('/admin/mainSite/partner/',
                         page[page.index('/admin/mainSite/bio/'):page.index('/admin/mainSite/badge/')])

"""The badge naming a sponsor's level, and the frame around a featured one."""
import re

from django.core.cache import cache
from django.test import TestCase

from accounts.models import User
from mainSite.models import BADGE_TEAL, BADGE_YELLOW, Partner

HOME_URL = '/'


def make_partner(name, **kwargs) -> Partner:
    return Partner.objects.create(name=name, logo='partners/logo.png', **kwargs)


def tile(response, name) -> str:
    """The one list item carrying this partner's logo."""
    body = response.content.decode()
    tiles = re.split(r'<li class="partner-strip__item', body)[1:]
    return next(chunk for chunk in tiles if f'alt="{name}"' in chunk)


class PartnerBadgeTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_a_partner_without_a_badge_gets_no_badge_markup(self):
        make_partner("Bez plakietki")

        self.assertNotIn('partner-strip__badge', tile(self.client.get(HOME_URL), "Bez plakietki"))

    def test_a_badge_is_drawn_above_the_logo(self):
        make_partner("Z plakietką", badge="Sponsor główny")

        drawn = tile(self.client.get(HOME_URL), "Z plakietką")

        self.assertIn("Sponsor główny", drawn)
        self.assertLess(drawn.index('partner-strip__badge'), drawn.index('partner-strip__logo'))

    def test_a_plain_badge_is_teal(self):
        make_partner("Turkusowa", badge="Partner")

        drawn = tile(self.client.get(HOME_URL), "Turkusowa")

        self.assertIn(BADGE_TEAL, drawn)
        self.assertNotIn(BADGE_YELLOW, drawn)

    def test_featuring_a_partner_turns_the_badge_yellow(self):
        make_partner("Żółta", badge="Sponsor główny", is_featured=True)

        drawn = tile(self.client.get(HOME_URL), "Żółta")

        self.assertIn(BADGE_YELLOW, drawn)
        self.assertNotIn(BADGE_TEAL, drawn)

    def test_featuring_a_partner_frames_the_tile(self):
        make_partner("W ramce", badge="Sponsor główny", is_featured=True)
        make_partner("Bez ramki", badge="Partner")

        response = self.client.get(HOME_URL)

        self.assertIn('partner-strip__item--featured', tile(response, "W ramce"))
        self.assertNotIn('partner-strip__item--featured', tile(response, "Bez ramki"))

    def test_featuring_a_partner_with_no_badge_draws_nothing(self):
        """A frame on its own says nothing, so it waits for a badge."""
        make_partner("Bez niczego", is_featured=True)

        drawn = tile(self.client.get(HOME_URL), "Bez niczego")

        self.assertNotIn('partner-strip__item--featured', drawn)
        self.assertNotIn('partner-strip__badge', drawn)

    def test_editing_a_partner_reaches_the_page(self):
        partner = make_partner("Zmienna", badge="Partner")
        self.client.get(HOME_URL)

        partner.badge = "Sponsor główny"
        partner.is_featured = True
        partner.save()

        drawn = tile(self.client.get(HOME_URL), "Zmienna")
        self.assertIn("Sponsor główny", drawn)
        self.assertIn(BADGE_YELLOW, drawn)


class PartnerLogoCellTests(TestCase):
    """A percentage cap needs a parent with a height to resolve against."""

    def setUp(self):
        cache.clear()

    def test_the_link_wrapper_stays_inside_the_logo_cell(self):
        """The cell is what caps the logo, so the anchor may not escape it."""
        make_partner("Linkowany", url='https://example.invalid/')

        drawn = tile(self.client.get(HOME_URL), "Linkowany")

        cell = drawn.index('partner-strip__logo')
        self.assertLess(cell, drawn.index('<a href="https://example.invalid/"'))
        self.assertLess(drawn.index('</a>'), drawn.index('</div>', cell))


class PartnerAdminTests(TestCase):
    """The list draws its own swatch, so every badge state must have paint."""

    def setUp(self):
        boss = User.objects.create_superuser(
            username='szefowa', email='szefowa@test.invalid', password='Testpass1!',
        )
        self.client.force_login(boss)

    def test_the_list_draws_every_badge_state(self):
        make_partner("Wyróżniony", badge="Sponsor główny", is_featured=True)
        make_partner("Zwykły", badge="Partner")
        make_partner("Bez plakietki")

        response = self.client.get('/admin/mainSite/partner/')

        self.assertEqual(response.status_code, 200)
        for name in ("Wyróżniony", "Zwykły", "Bez plakietki"):
            self.assertContains(response, name)

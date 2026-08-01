from django.core.exceptions import ValidationError
from django.test import TestCase

from seminars.models import DEFAULT_GROUP_COLOR, SeminarGroup


class SeminarGroupCalendarConfigTests(TestCase):
    def test_colour_must_be_a_six_digit_hex_value(self):
        with self.assertRaises(ValidationError):
            SeminarGroup(name="Grupa", color="czerwony").full_clean()

    def test_blank_colour_is_allowed_and_means_default(self):
        group = SeminarGroup(name="Grupa")

        group.full_clean()

        self.assertEqual(group.display_color, DEFAULT_GROUP_COLOR)

    def test_configured_colour_is_used(self):
        self.assertEqual(SeminarGroup(name="Grupa", color="#0E7C9B").display_color, "#0E7C9B")

    def test_short_label_falls_back_to_the_full_name(self):
        self.assertEqual(SeminarGroup(name="OM średnia").display_short_label, "OM średnia")

    def test_short_label_is_used_when_set(self):
        group = SeminarGroup(name="warsztaty II etap", short_label="warsztaty")

        self.assertEqual(group.display_short_label, "warsztaty")

    def test_display_dict_carries_the_colour_for_the_group_tiles(self):
        group = SeminarGroup.objects.create(
            name="OM średnia", color="#0E7C9B", lead="Koło", description="Opis",
        )

        self.assertEqual(group.display_dict()['color'], "#0E7C9B")

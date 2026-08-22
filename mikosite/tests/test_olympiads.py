from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from olympiads.models import Olympiad, OlympiadStage
from olympiads.serializers import OlympiadStageSerializer


class DefaultOlympiadTests(TestCase):
    def test_olympiads_miko_prepares_for_are_seeded(self):
        self.assertEqual(
            set(Olympiad.objects.values_list('name', flat=True)),
            {"Olimpiada Matematyczna", "Olimpiada Informatyczna", "Olimpiada AI"},
        )

    def test_seeded_olympiads_are_ordered_for_display(self):
        self.assertEqual(
            list(Olympiad.objects.values_list('short_name', flat=True)),
            ["OM", "OI", "AI"],
        )


class OlympiadStageTests(TestCase):
    def setUp(self):
        self.olympiad = Olympiad.objects.get(name="Olimpiada Matematyczna")

    def test_stage_name_is_free_text(self):
        stage = OlympiadStage.objects.create(
            olympiad=self.olympiad, name="Zawody drużynowe",
            date_begin=date(2026, 3, 10), date_end=date(2026, 3, 11),
        )

        self.assertEqual(OlympiadStageSerializer(stage).data['title'], "OM – Zawody drużynowe")

    def test_stage_defaults_to_the_second_round(self):
        stage = OlympiadStage.objects.create(
            olympiad=self.olympiad, date_begin=date(2026, 3, 10), date_end=date(2026, 3, 11),
        )

        self.assertEqual(stage.name, "II etap")

    def test_the_same_stage_may_run_in_several_school_years(self):
        OlympiadStage.objects.create(olympiad=self.olympiad, name="Finał",
                                     date_begin=date(2026, 4, 8), date_end=date(2026, 4, 10))
        next_year = OlympiadStage(olympiad=self.olympiad, name="Finał",
                                  date_begin=date(2027, 4, 7), date_end=date(2027, 4, 9))

        next_year.full_clean()

    def test_end_before_begin_is_rejected(self):
        stage = OlympiadStage(olympiad=self.olympiad, name="II etap",
                              date_begin=date(2026, 3, 10), date_end=date(2026, 3, 9))

        with self.assertRaises(ValidationError):
            stage.full_clean()

    def test_overlapping_runs_of_the_same_stage_are_rejected(self):
        OlympiadStage.objects.create(olympiad=self.olympiad, name="II etap",
                                     date_begin=date(2026, 3, 10), date_end=date(2026, 3, 12))
        overlapping = OlympiadStage(olympiad=self.olympiad, name="II etap",
                                    date_begin=date(2026, 3, 12), date_end=date(2026, 3, 14))

        with self.assertRaises(ValidationError):
            overlapping.full_clean()

    def test_different_stages_may_share_dates(self):
        OlympiadStage.objects.create(olympiad=self.olympiad, name="II etap",
                                     date_begin=date(2026, 3, 10), date_end=date(2026, 3, 12))
        final = OlympiadStage(olympiad=self.olympiad, name="Finał",
                              date_begin=date(2026, 3, 10), date_end=date(2026, 3, 12))

        final.full_clean()

    def test_stage_without_a_link_falls_back_to_the_olympiad_website(self):
        self.olympiad.website_url = "https://example.invalid/om/"
        self.olympiad.save()
        stage = OlympiadStage.objects.create(olympiad=self.olympiad, name="Finał",
                                             date_begin=date(2026, 3, 10), date_end=date(2026, 3, 14))

        self.assertEqual(OlympiadStageSerializer(stage).data['url'], "https://example.invalid/om/")

    def test_stage_link_wins_over_the_olympiad_website(self):
        self.olympiad.website_url = "https://example.invalid/om/"
        self.olympiad.save()
        stage = OlympiadStage.objects.create(
            olympiad=self.olympiad, name="Finał", url="https://example.invalid/final/",
            date_begin=date(2026, 3, 10), date_end=date(2026, 3, 14),
        )

        self.assertEqual(OlympiadStageSerializer(stage).data['url'], "https://example.invalid/final/")

    def test_stages_are_counted_for_the_admin_listing(self):
        OlympiadStage.objects.create(olympiad=self.olympiad, name="II etap",
                                     date_begin=date(2026, 3, 10), date_end=date(2026, 3, 12))
        OlympiadStage.objects.create(olympiad=self.olympiad, name="Finał",
                                     date_begin=date(2026, 4, 8), date_end=date(2026, 4, 10))

        self.assertEqual(self.olympiad.stage_count, 2)

    def test_deleting_an_olympiad_removes_its_stages(self):
        OlympiadStage.objects.create(olympiad=self.olympiad, name="II etap",
                                     date_begin=date(2026, 3, 10), date_end=date(2026, 3, 12))

        self.olympiad.delete()

        self.assertEqual(OlympiadStage.objects.count(), 0)

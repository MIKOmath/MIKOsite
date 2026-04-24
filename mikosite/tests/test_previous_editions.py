from datetime import date, time, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from seminars.models import PreviousEdition, PreviousEditionMilestone, Seminar
from seminars.views import polish_kolo_unit, polish_year_unit, rounded_years_since


class PreviousEditionTests(TestCase):
    def test_school_year_label_member_label_and_seminar_count_are_derived(self):
        edition = PreviousEdition.objects.create(
            start_date=date(2023, 9, 1),
            end_date=date(2024, 8, 31),
            member_count=2000,
            member_count_is_estimate=True,
        )
        Seminar.objects.create(
            date=date(2023, 9, 1),
            time=time(17, 0),
            duration=timedelta(hours=1),
            theme="Opening seminar",
        )
        Seminar.objects.create(
            date=date(2024, 8, 31),
            time=time(17, 0),
            duration=timedelta(hours=1),
            theme="Closing seminar",
        )
        Seminar.objects.create(
            date=date(2024, 9, 1),
            time=time(17, 0),
            duration=timedelta(hours=1),
            theme="Next edition seminar",
        )

        self.assertEqual(edition.school_year_label, "Rok szkolny 2023/24")
        self.assertEqual(edition.member_count_label, "2000+")
        self.assertEqual(edition.seminar_count, 2)

    def test_overlapping_edition_ranges_are_rejected(self):
        PreviousEdition.objects.create(
            start_date=date(2023, 9, 1),
            end_date=date(2024, 8, 31),
        )
        overlapping = PreviousEdition(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

        with self.assertRaises(ValidationError):
            overlapping.full_clean()

    def test_rounded_experience_years_rounds_up_from_start_date(self):
        self.assertEqual(rounded_years_since(date(2023, 9, 1), today=date(2026, 4, 22)), 3)

    def test_polish_year_unit_uses_babel_plural_rules(self):
        self.assertEqual(polish_year_unit(1), "rok")
        self.assertEqual(polish_year_unit(2), "lata")
        self.assertEqual(polish_year_unit(5), "lat")
        self.assertEqual(polish_year_unit(22), "lata")

    def test_polish_kolo_unit_uses_babel_plural_rules(self):
        self.assertEqual(polish_kolo_unit(1), "koło")
        self.assertEqual(polish_kolo_unit(2), "koła")
        self.assertEqual(polish_kolo_unit(5), "kół")
        self.assertEqual(polish_kolo_unit(22), "koła")

    def test_previous_editions_page_displays_public_editions(self):
        edition = PreviousEdition.objects.create(
            start_date=date(2023, 9, 1),
            end_date=date(2024, 8, 31),
            member_count=2000,
            member_count_is_estimate=True,
        )
        PreviousEditionMilestone.objects.create(
            edition=edition,
            date=date(2023, 10, 15),
            title="Pierwszy komplet materiałów",
            description="Uczniowie opublikowali materiały do pierwszego działu.",
            material_icon="library_books",
        )
        PreviousEditionMilestone.objects.create(
            edition=edition,
            date=date(2023, 10, 20),
            show_date=False,
            title="Kamień milowy bez widocznej daty",
            material_icon="flag",
        )
        PreviousEdition.objects.create(
            start_date=date(2022, 9, 1),
            end_date=date(2023, 8, 31),
            is_published=False,
        )

        response = self.client.get("/editions/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rok szkolny 2023/24")
        self.assertContains(response, "2000+")
        self.assertContains(response, "W przygotowaniu")
        self.assertContains(response, "15.10.2023")
        self.assertContains(response, "Pierwszy komplet materiałów")
        self.assertContains(response, "Kamień milowy bez widocznej daty")
        self.assertContains(response, "library_books")
        self.assertNotContains(response, "20.10.2023")
        self.assertNotContains(response, "01.09.2023")
        self.assertNotContains(response, "Archiwum MIKO")
        self.assertNotContains(response, "Rok szkolny 2022/23")

    def test_milestone_link_url_is_rendered_when_defined(self):
        edition = PreviousEdition.objects.create(
            start_date=date(2023, 9, 1),
            end_date=date(2024, 8, 31),
        )
        milestone = PreviousEditionMilestone.objects.create(
            edition=edition,
            date=date(2023, 10, 15),
            title="Opis projektu",
            material_icon="library_books",
            link_url="/about/",
        )

        response = self.client.get("/editions/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, milestone.title)
        self.assertContains(response, 'href="/about/"', html=False)

    def test_milestone_date_must_belong_to_edition(self):
        edition = PreviousEdition.objects.create(
            start_date=date(2023, 9, 1),
            end_date=date(2024, 8, 31),
        )
        milestone = PreviousEditionMilestone(
            edition=edition,
            date=date(2024, 9, 1),
            title="Poza edycją",
            material_icon="flag",
        )

        with self.assertRaises(ValidationError):
            milestone.full_clean()

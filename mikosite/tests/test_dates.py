from datetime import date

from django.test import TestCase

from mikosite.dates import format_day_range


class FormatDayRangeTests(TestCase):
    def test_single_day_drops_the_range(self):
        self.assertEqual(format_day_range(date(2026, 8, 17), date(2026, 8, 17)), "17 sierpnia")

    def test_range_inside_one_month_names_the_month_once(self):
        self.assertEqual(format_day_range(date(2026, 8, 17), date(2026, 8, 22)), "17-22 sierpnia")

    def test_range_across_months_names_both(self):
        self.assertEqual(format_day_range(date(2026, 7, 30), date(2026, 8, 2)), "30 lipca - 2 sierpnia")

    def test_range_across_years_includes_the_year(self):
        self.assertEqual(
            format_day_range(date(2026, 12, 30), date(2027, 1, 2)),
            "30 grudnia 2026 - 2 stycznia 2027",
        )

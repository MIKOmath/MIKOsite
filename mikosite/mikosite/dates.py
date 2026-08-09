from datetime import datetime, timedelta

from babel.dates import format_date

from django.conf import settings
from django.utils import timezone


def rounded_years_since(start_date, today=None) -> int:
    today = today or timezone.localdate()
    if today <= start_date:
        return 0
    return round((today - start_date).days / 365.2425)


def polish_year_unit(years, locale=settings.BABEL_LOCALE) -> str:
    plural_form = locale.plural_form(years)
    if plural_form == 'one':
        return 'rok'
    if plural_form == 'few':
        return 'lata'
    return 'lat'


def polish_partner_unit(count, locale=settings.BABEL_LOCALE) -> str:
    plural_form = locale.plural_form(count)
    if plural_form == 'one':
        return 'partner'
    if plural_form == 'few':
        return 'partnerzy'
    return 'partnerów'


def seconds_until_next_midnight() -> int:
    now = datetime.now()
    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((next_midnight - now).total_seconds())


def format_day_range(date_begin, date_end, locale=settings.BABEL_LOCALE) -> str:
    """Polish label for a (possibly single day) date range, e.g. "17-22 sierpnia"."""
    if date_begin == date_end:
        return format_date(date_begin, format='d MMMM', locale=locale)

    if date_begin.year != date_end.year:
        return f"{format_date(date_begin, format='d MMMM y', locale=locale)} - " \
               f"{format_date(date_end, format='d MMMM y', locale=locale)}"

    if date_begin.month == date_end.month:
        start_day = format_date(date_begin, format='d', locale=locale)
        return f"{start_day}-{format_date(date_end, format='d MMMM', locale=locale)}"

    return f"{format_date(date_begin, format='d MMMM', locale=locale)} - " \
           f"{format_date(date_end, format='d MMMM', locale=locale)}"

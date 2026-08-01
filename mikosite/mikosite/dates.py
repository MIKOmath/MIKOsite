from datetime import datetime, timedelta

from babel.dates import format_date

from django.conf import settings


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

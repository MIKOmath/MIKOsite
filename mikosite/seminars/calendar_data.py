"""Aggregated payload behind the calendar on /kolo/.

The calendar asks for one visible grid range at a time, so a single request has to
carry everything drawn on that range: seminars, multi-day in-person events that
registration is held for, and multi-day olympiad stages.
"""
import time

from django.core.cache import cache
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from mainSite.models import RegistrationEvent
from mikosite.dates import seconds_until_next_midnight
from olympiads.models import Olympiad, OlympiadStage

from .models import Seminar, SeminarGroup

CALENDAR_VERSION_CACHE_KEY = 'calendar-payload-version'
CALENDAR_PAYLOAD_MAX_TTL = 900  # 15 minutes
MAX_CALENDAR_RANGE_DAYS = 62


def get_calendar_version() -> int:
    """Namespace for cached payloads, bumped whenever displayed data changes.

    Seeding from the wall clock means an evicted counter starts a fresh namespace
    instead of colliding with payloads cached under an earlier counter value.
    """
    version = cache.get(CALENDAR_VERSION_CACHE_KEY)
    if version is None:
        version = int(time.time())
        cache.set(CALENDAR_VERSION_CACHE_KEY, version, None)
    return version


def calendar_cache_key(start_date, end_date) -> str:
    return f"calendar-payload:{get_calendar_version()}:{start_date.isoformat()}:{end_date.isoformat()}"


def bump_calendar_version():
    try:
        cache.incr(CALENDAR_VERSION_CACHE_KEY)
    except ValueError:
        cache.set(CALENDAR_VERSION_CACHE_KEY, int(time.time()), None)


def build_calendar_payload(start_date, end_date) -> dict:
    """Everything drawn on the calendar between the two dates, both inclusive."""
    today = timezone.localdate()

    seminars = (
        Seminar.objects
        .filter(date__gte=start_date, date__lte=end_date)
        .select_related('group')
        .prefetch_related('tutors')
        .order_by('date', 'time')
    )

    registration_events = (
        RegistrationEvent.objects
        .filter(date_begin__lte=end_date, date_end__gte=start_date)
        .order_by('date_begin', 'date_end', 'pk')
    )

    olympiad_stages = (
        OlympiadStage.objects
        .filter(date_begin__lte=end_date, date_end__gte=start_date, olympiad__is_active=True)
        .select_related('olympiad')
    )

    return {
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'seminars': [seminar.calendar_dict() for seminar in seminars],
        'registration_events': [event.calendar_dict(today=today) for event in registration_events],
        'olympiad_stages': [stage.calendar_dict() for stage in olympiad_stages],
    }


def get_calendar_payload(start_date, end_date) -> dict:
    cache_key = calendar_cache_key(start_date, end_date)
    payload = cache.get(cache_key)
    if payload is None:
        payload = build_calendar_payload(start_date, end_date)
        # Registration windows are evaluated against today, so never cache past midnight.
        cache.set(cache_key, payload, min(CALENDAR_PAYLOAD_MAX_TTL, seconds_until_next_midnight()))
    return payload


@receiver(post_save, sender=Seminar)
@receiver(post_delete, sender=Seminar)
@receiver(post_save, sender=SeminarGroup)
@receiver(post_delete, sender=SeminarGroup)
@receiver(post_save, sender=Olympiad)
@receiver(post_delete, sender=Olympiad)
@receiver(post_save, sender=OlympiadStage)
@receiver(post_delete, sender=OlympiadStage)
@receiver(post_save, sender=RegistrationEvent)
@receiver(post_delete, sender=RegistrationEvent)
@receiver(m2m_changed, sender=Seminar.tutors.through)
def clear_calendar_cache(sender, **kwargs):
    bump_calendar_version()

from datetime import datetime, timedelta

from django.core.cache import cache
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver
from django.shortcuts import render

from mainSite.models import RegistrationEvent, Post
from seminars.models import Seminar

UPCOMING_SEMINARS_CACHE_KEY = 'upcoming-seminars-display-data'
UPCOMING_SEMINARS_MAX_TTL = 86400  # 1 day
MAINSITE_POSTS_CACHE_KEY = 'mainsite-posts-display-data'
MAINSITE_POSTS_MAX_TTL = 86400
ACTIVE_REGISTRATION_CACHE_KEY = 'active-registration-display-data'


def seconds_until_next_midnight() -> int:
    now = datetime.now()
    next_midnight = (now + timedelta(days=1)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return int((next_midnight - now).total_seconds())


def get_upcoming_seminars_data():
    data = cache.get(UPCOMING_SEMINARS_CACHE_KEY)
    if data is None:
        next_seminars = Seminar.fetch_upcoming()
        if next_seminars:
            time_to_next_seminar = (
                next_seminars[0].start_timestamp - datetime.now()
            ).total_seconds()
        else:
            time_to_next_seminar = UPCOMING_SEMINARS_MAX_TTL

        data = [seminar.display_dict() for seminar in next_seminars]
        cache.set(
            UPCOMING_SEMINARS_CACHE_KEY,
            data,
            min(time_to_next_seminar, UPCOMING_SEMINARS_MAX_TTL),
        )
    return data


@receiver(post_save, sender=Seminar)
@receiver(post_delete, sender=Seminar)
@receiver(m2m_changed, sender=Seminar.tutors.through)
def clear_upcoming_seminars_cache(sender, **kwargs):
    cache.delete(UPCOMING_SEMINARS_CACHE_KEY)


def get_posts_data():
    data = cache.get(MAINSITE_POSTS_CACHE_KEY)
    if data is None:
        posts = Post.objects.order_by('-date', '-time').prefetch_related('authors', 'images')
        data = [post.display_dict() for post in posts]
        cache.set(MAINSITE_POSTS_CACHE_KEY, data, MAINSITE_POSTS_MAX_TTL)
    return data


@receiver(post_save, sender=Post)
@receiver(post_delete, sender=Post)
@receiver(m2m_changed, sender=Post.authors.through)
@receiver(m2m_changed, sender=Post.images.through)
def clear_posts_cache(sender, **kwargs):
    cache.delete(MAINSITE_POSTS_CACHE_KEY)


def get_active_registration_event_data():
    data = cache.get(ACTIVE_REGISTRATION_CACHE_KEY)
    if data is None:
        today = datetime.today()
        event = (
            RegistrationEvent.objects
            .filter(registration_begin__lte=today, registration_end__gte=today)
            .order_by('registration_end', 'date_begin', 'pk')
            .first()
        )
        data = event.display_dict() if event else None
        cache.set(
            ACTIVE_REGISTRATION_CACHE_KEY,
            data,
            seconds_until_next_midnight(),
        )
    return data


@receiver(post_save, sender=RegistrationEvent)
@receiver(post_delete, sender=RegistrationEvent)
def clear_active_registration_event_cache(sender, **kwargs):
    cache.delete(ACTIVE_REGISTRATION_CACHE_KEY)


def index(request):
    context = {
        "posts": get_posts_data,
        "events": get_upcoming_seminars_data,
        "registration_event": get_active_registration_event_data,
        "user": request.user,
    }
    return render(request, "index.html", context)


def about(request):
    return render(request, "about.html")


def roadmap(request):
    return render(request, "roadmap.html")

from datetime import date, datetime

from django.core.cache import cache
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.html import strip_tags
from django.utils.text import Truncator

from django.core.paginator import Paginator

from mainSite.models import Partner, RegistrationEvent, Post
from mikosite.dates import (
    polish_partner_unit,
    polish_year_unit,
    rounded_years_since,
    seconds_until_next_midnight,
)
from seminars.models import PreviousEdition, Seminar

UPCOMING_SEMINARS_CACHE_KEY = 'upcoming-seminars-display-data'
UPCOMING_SEMINARS_MAX_TTL = 86400  # 1 day
UPCOMING_SEMINAR_DESCRIPTION_PREVIEW_LENGTH = 250
MAINSITE_POSTS_CACHE_KEY = 'mainsite-posts-display-data'
MAINSITE_POSTS_MAX_TTL = 86400
ACTIVE_REGISTRATION_CACHE_KEY = 'active-registration-display-data'
PARTNERS_CACHE_KEY = 'mainsite-partners-display-data'
PARTNERS_MAX_TTL = 86400
HISTORY_CACHE_KEY = 'mainsite-history-display-data'
HOMEPAGE_POST_MAX = 3
HOMEPAGE_POST_BUDGET = 1600  # characters of announcement text the band will carry
PARTNERS_HOME_LIMIT = 12
ANNOUNCEMENTS_PER_PAGE = 10
DEFAULT_HISTORY_START_DATE = date(2023, 9, 1)


def build_upcoming_seminar_display_data(seminar: Seminar) -> dict:
    seminar_data = seminar.display_dict()
    description = seminar_data.get('description')
    normalized_description = ' '.join(description.split()) if description else None

    short_description = (
        Truncator(normalized_description).chars(
            UPCOMING_SEMINAR_DESCRIPTION_PREVIEW_LENGTH,
            truncate='...',
        )
        if normalized_description
        else None
    )

    seminar_data.update({
        'id': seminar.pk,
        'short_description': short_description,
        'description_is_truncated': bool(
            normalized_description and short_description != normalized_description
        ),
    })
    return seminar_data


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

        data = [build_upcoming_seminar_display_data(seminar) for seminar in next_seminars]
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


def select_homepage_posts(posts: list) -> list:
    """As many announcements as fit a text budget, so one long post does not
    stretch the band the way three short ones would not."""
    selected = []
    used = 0
    for post in posts[:HOMEPAGE_POST_MAX]:
        length = len(strip_tags(post.get('content') or '')) + len(post.get('subtitle') or '')
        if selected and used + length > HOMEPAGE_POST_BUDGET:
            break
        selected.append(post)
        used += length
    return selected


def get_partners_data():
    data = cache.get(PARTNERS_CACHE_KEY)
    if data is None:
        data = [
            partner.display_dict()
            for partner in Partner.objects.filter(is_published=True)
        ]
        cache.set(PARTNERS_CACHE_KEY, data, PARTNERS_MAX_TTL)
    return data


@receiver(post_save, sender=Partner)
@receiver(post_delete, sender=Partner)
def clear_partners_cache(sender, **kwargs):
    cache.delete(PARTNERS_CACHE_KEY)


def get_history_data():
    """Years since the first edition, so the figure keeps itself up to date."""
    data = cache.get(HISTORY_CACHE_KEY)
    if data is None:
        first_edition = (
            PreviousEdition.objects.filter(is_published=True).order_by('start_date').first()
        )
        start_date = first_edition.start_date if first_edition else DEFAULT_HISTORY_START_DATE
        years = rounded_years_since(start_date)
        data = {'experience_years': years, 'experience_year_unit': polish_year_unit(years)}
        cache.set(HISTORY_CACHE_KEY, data, seconds_until_next_midnight())
    return data


@receiver(post_save, sender=PreviousEdition)
@receiver(post_delete, sender=PreviousEdition)
def clear_history_cache(sender, **kwargs):
    cache.delete(HISTORY_CACHE_KEY)


def empty_error_response(status: int) -> HttpResponse:
    """Return the status only; nginx replaces error page bodies anyway.

    Rendering a template here would pull in the site header, resolve
    request.user and query the database. Under ASGI, Django renders error
    responses on a shared executor thread whose connections it never closes,
    so that query checks a connection out of the psycopg pool and never
    returns it (Django #36027).
    """
    return HttpResponse(status=status)


def bad_request(request, exception):
    return empty_error_response(400)


def permission_denied(request, exception):
    return empty_error_response(403)


def page_not_found(request, exception):
    return empty_error_response(404)


def server_error(request):
    return empty_error_response(500)


def index(request):
    posts = get_posts_data()
    shown_posts = select_homepage_posts(posts)
    partners = get_partners_data()
    partners_hidden = max(0, len(partners) - PARTNERS_HOME_LIMIT)

    context = {
        "posts": shown_posts,
        "has_more_posts": len(posts) > len(shown_posts),
        "events": get_upcoming_seminars_data,
        "registration_event": get_active_registration_event_data,
        "history": get_history_data,
        "partners": partners[:PARTNERS_HOME_LIMIT],
        "partners_hidden": partners_hidden,
        "partners_hidden_unit": polish_partner_unit(partners_hidden),
        "user": request.user,
    }
    return render(request, "index.html", context)


def announcements(request):
    paginator = Paginator(get_posts_data(), ANNOUNCEMENTS_PER_PAGE)
    page = paginator.get_page(request.GET.get('strona'))
    return render(request, "announcements.html", {"page": page, "user": request.user})


def about(request):
    return render(request, "about.html")


def roadmap(request):
    return render(request, "roadmap.html")

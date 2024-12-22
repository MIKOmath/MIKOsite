from datetime import datetime
from django.core.cache import cache
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.shortcuts import render

from mainSite.models import Post
from seminars.models import Seminar


UPCOMING_SEMINARS_CACHE_KEY = 'upcoming-seminars-display-data'
UPCOMING_SEMINARS_MAX_TTL = 86400  # 1 day
MAINSITE_POSTS_CACHE_KEY = 'mainsite-posts-display-data'
MAINSITE_POSTS_MAX_TTL = 86400


def get_upcoming_seminars_data():
    data = cache.get(UPCOMING_SEMINARS_CACHE_KEY)
    if data is None:
        next_seminars = Seminar.fetch_upcoming()
        if next_seminars:
            time_to_next_seminar = (next_seminars[0].start_timestamp - datetime.now()).total_seconds()
        else:
            time_to_next_seminar = UPCOMING_SEMINARS_MAX_TTL

        data = [seminar.display_dict() for seminar in next_seminars]
        cache.set(UPCOMING_SEMINARS_CACHE_KEY, data, min(time_to_next_seminar, UPCOMING_SEMINARS_MAX_TTL))

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


def index(request):
    context = {
        "posts": get_posts_data,
        "events": get_upcoming_seminars_data,
        "user": request.user
    }
    return render(request, "index.html", context)


def about(request):
    return render(request, "about.html")


def roadmap(request):
    return render(request, "roadmap.html")

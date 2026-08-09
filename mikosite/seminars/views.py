from django.conf import settings
from django.dispatch import receiver
from django.shortcuts import render
from django.db.models import Q
from django.db.models.signals import post_save, post_delete
from django.core.cache import cache

from .models import (
    PreviousEdition,
    Seminar,
    SeminarGroup,
)


SEMINAR_GROUPS_CACHE_KEY = 'seminar-groups-display-data-v2'
SEMINAR_GROUPS_MAX_TTL = 604800  # 1 week


def polish_kolo_unit(count, locale=settings.BABEL_LOCALE):
    plural_form = locale.plural_form(count)
    if plural_form == 'one':
        return 'koło'
    if plural_form == 'few':
        return 'koła'
    return 'kół'


def get_seminar_group_data():
    data = cache.get(SEMINAR_GROUPS_CACHE_KEY)
    if data is None:
        groups = (SeminarGroup.objects.all().exclude(
            Q(lead__isnull=True) | Q(lead='') | Q(description__isnull=True) | Q(description=''))
                  .order_by('default_difficulty', 'lead'))
        data = [group.display_dict() for group in groups]
        cache.set(SEMINAR_GROUPS_CACHE_KEY, data, SEMINAR_GROUPS_MAX_TTL)

    return data


@receiver(post_save, sender=SeminarGroup)
@receiver(post_delete, sender=SeminarGroup)
def clear_seminar_groups_cache(sender, **kwargs):
    cache.delete(SEMINAR_GROUPS_CACHE_KEY)


def informacje(request):
    return render(request, "informacje.html", {"groups": get_seminar_group_data()})


def previous_editions(request):
    editions = PreviousEdition.objects.filter(is_published=True).prefetch_related('milestones').order_by('-start_date')
    edition_cards = []
    for edition in editions:
        seminar_count = edition.seminar_count
        edition_cards.append({
            "edition": edition,
            "milestones": list(edition.milestones.all()),
            "seminar_count": seminar_count,
            "seminar_unit": polish_kolo_unit(seminar_count),
        })

    return render(request, "previous_editions.html", {"edition_cards": edition_cards})

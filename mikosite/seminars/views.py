from django.dispatch import receiver
from django.shortcuts import render
from django.db.models import Q
from django.db.models.signals import post_save, post_delete
from django.core.cache import cache

from .models import Seminar, SeminarGroup


SEMINAR_GROUPS_CACHE_KEY = 'seminar-groups-display-data'
SEMINAR_GROUPS_MAX_TTL = 604800  # 1 week

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
    seminars = Seminar.objects.all().order_by('date', 'time').select_related('group').prefetch_related('tutors')
    for seminar in seminars:
        seminar.display = seminar.display_dict()

    return render(request, "informacje.html", {"groups": get_seminar_group_data, "seminars": seminars})

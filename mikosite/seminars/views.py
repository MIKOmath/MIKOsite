from django.shortcuts import render
from django.db.models import Q
from django.template.defaultfilters import stringfilter
from django.template.defaulttags import register
from django.utils.safestring import mark_safe
from .models import Seminar, SeminarGroup
from babel import Locale


@register.filter
@stringfilter
def split(value, key):
    return value.split(key)


def informacje(request):
    locale = Locale('pl_PL')

    groups = (SeminarGroup.objects.all().exclude(
        Q(lead__isnull=True) | Q(lead='') | Q(description__isnull=True) | Q(description=''))
        .order_by('default_difficulty', 'lead'))

    for group in groups:
        group.lead = mark_safe(group.lead)
        group.desc_snippets = [mark_safe(snippet) for snippet in group.description.split('\n') if snippet]

    seminars = Seminar.objects.all().order_by('date', 'time').select_related('group').prefetch_related('tutors')
    for seminar in seminars:
        seminar.display = seminar.display_dict(locale)

    return render(request, "informacje.html", {"groups": groups, "seminars": seminars})

from django.shortcuts import render
from .models import Seminar
from babel import Locale


def informacje(request):
    locale = Locale('pl_PL')

    seminars = Seminar.objects.all().order_by('date', 'time')
    for seminar in seminars:
        seminar.display = seminar.display_dict(locale)

    return render(request, "informacje.html", {"seminars": seminars})

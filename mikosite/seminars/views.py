from django.shortcuts import render
from .models import Seminar


def informacje(request):
    seminars = Seminar.objects.all().order_by('date', 'time')
    return render(request, "informacje.html", {"seminars": seminars})

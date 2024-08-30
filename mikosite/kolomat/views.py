from django.shortcuts import render
from .models import Kolo


# @cache_page(60*15)
def informacje(request):
    kolka = Kolo.objects.all().order_by('date', 'time')
    return render(request, "informacje.html", {"kolka": kolka})

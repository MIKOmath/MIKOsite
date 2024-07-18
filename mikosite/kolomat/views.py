from django.shortcuts import render
from django.contrib import messages
from accounts.models import User
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.conf import settings
from .models import Kolo
from taggit.models import Tag
from fuzzywuzzy import fuzz
from datetime import datetime
from pytz import timezone
import pytz
from django.views.decorators.cache import cache_page



# Create your views here.

# @cache_page(60*15)
def informacje(request):
    kolka = Kolo.objects.all().order_by('date', 'time')
    return render(request, "informacje.html", {"kolka": kolka})

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


# Create your views here.

def informacje(request):
    kolka = Kolo.objects.all()

    for i in kolka:
        print(i.date)

    return render(request, "informacje.html", {"kolka": kolka})

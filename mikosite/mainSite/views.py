from django.shortcuts import render
from mainSite.models import Post
from django.http import HttpResponse
from kolomat.models import Kolo
from datetime import datetime, date, time

# Create your views here.


def index(request):

    today = date.today()
    now = datetime.now().time()

    # Get all future Kolo instances

    future_kolos = [
        kolo for kolo in Kolo.objects.all()
        if kolo.date and kolo.time and
           (kolo.date > today or (kolo.date == today and kolo.time > now))
    ]

    if not future_kolos:
        next_kolo_instances = []
    else:

        future_kolos.sort(key=lambda k: datetime.combine(k.date, k.time))

        next_date = future_kolos[0].date

        next_kolo_instances = [
            kolo for kolo in future_kolos if kolo.date == next_date
        ]




    posts = Post.objects.all()
    reversed_posts = reversed(posts)
    context = {"posts": reversed_posts, "eventy" : next_kolo_instances}


    context["user"] = request.user
    return render(request, "index.html", context)


def about(request):

    return render(request, "about.html")

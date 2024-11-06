from django.shortcuts import render
from mainSite.models import Post
from seminars.models import Seminar
from datetime import datetime, date
from babel import Locale


def index(request):
    today = date.today()
    now = datetime.now().time()
    locale = Locale('pl_PL')

    # fetch all future seminars
    future_seminars = Seminar.objects.filter(date__gt=today).union(
        Seminar.objects.filter(date=today, time__gt=now)).order_by('date', 'time')

    # get next 3 seminars or all that happen on the same (earliest) day
    next_date = future_seminars[0].date if future_seminars else None
    next_seminars = [kolo for kolo in future_seminars if kolo.date == next_date]
    if len(next_seminars) < 3:
        next_seminars = future_seminars[:3]

    event_data = [seminar.display_dict(locale) for seminar in next_seminars]

    post_data = [post.display_dict(locale) for post in Post.objects.all()]
    post_data.reverse()

    context = {
        "posts": post_data,
        "events": event_data,
        "user": request.user
    }
    return render(request, "index.html", context)


def about(request):
    return render(request, "about.html")


def roadmap(request):
    return render(request, "roadmap.html")

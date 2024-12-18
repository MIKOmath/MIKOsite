from datetime import datetime, date
from babel import Locale

from django.shortcuts import render
from mainSite.models import Post
from seminars.models import Seminar


def index(request):
    today = date.today()
    now = datetime.now().time()
    locale = Locale('pl_PL')

    next_seminars = Seminar.fetch_upcoming(today, now)
    event_data = [seminar.display_dict(locale) for seminar in next_seminars]

    posts = Post.objects.order_by('-date', '-time').prefetch_related('authors', 'images')
    post_data = [post.display_dict(locale) for post in posts]

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

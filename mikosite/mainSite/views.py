from django.shortcuts import render
from mainSite.models import Post
from seminars.models import Seminar
from datetime import datetime, date
from babel.dates import format_date, format_time
from babel import Locale


# @cache_page(60*5)
def index(request):
    today = date.today()
    now = datetime.now().time()
    locale = Locale('pl_PL')

    # Get all future Seminar instances
    future_seminars = [
        seminar for seminar in Seminar.objects.all()
        if seminar.date and seminar.time and (seminar.date > today or (seminar.date == today and seminar.time > now))
    ]

    if not future_seminars:
        next_seminars = []
    else:
        future_seminars.sort(key=lambda k: datetime.combine(k.date, k.time))
        next_date = future_seminars[0].date
        next_seminars = [seminar for seminar in future_seminars if seminar.date == next_date]

    # If there are less than 3 events on the next date, try to get one more recent event
    if len(next_seminars) < 3:
        remaining_seminars = [kolo for kolo in future_seminars if kolo.date > next_date]
        if remaining_seminars:
            next_seminars.append(remaining_seminars[0])

    event_data = []
    for seminar in next_seminars:
        start_time = format_time(seminar.time, format='HH:mm', locale=locale)
        end_time = format_time((datetime.combine(date.today(), seminar.time) + seminar.duration).time(), format='HH:mm',
                               locale=locale)
        polish_date = format_date(seminar.date, format='d MMMM y', locale=locale)

        event_data.append({
            'theme': seminar.theme,
            'date': polish_date,
            'time_range': f"{start_time} - {end_time}",
            'duration': seminar.duration,
            'tutors': seminar.tutors.all(),
            'description': seminar.description,
            'image': seminar.image,
            'file': seminar.file,
            'level': seminar.level,
            'finished': seminar.finished,
        })

    post_data = [post.display_dict(locale) for post in Post.objects.all()]
    post_data.reverse()

    context = {
        "posts": post_data,
        "eventy": event_data,
        "user": request.user
    }
    return render(request, "index.html", context)


def about(request):
    return render(request, "about.html")


def roadmap(request):
    return render(request, "roadmap.html")

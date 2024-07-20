from django.shortcuts import render
from mainSite.models import Post
from django.http import HttpResponse
from kolomat.models import Kolo
from datetime import datetime, date, time
from django.views.decorators.cache import cache_page

# Create your views here.

# @cache_page(60*5)
def index(request):

    today = date.today()
    now = datetime.now().time()

    months = [
        ("stycznia"), ("lutego"), ("marca"), ("kwietnia"), ("maja"), ("czerwca"),
        ("lipca"), ("sierpnia"), ("września"), ("października"), ("listopada"), ("grudnia")
    ]

    # Get all future Kolo instances
    future_kolos = [
        kolo for kolo in Kolo.objects.all()
        if kolo.date and kolo.time and (kolo.date > today or (kolo.date == today and kolo.time > now))
    ]

    if not future_kolos:
        next_kolo_instances = []
    else:
        future_kolos.sort(key=lambda k: datetime.combine(k.date, k.time))
        next_date = future_kolos[0].date
        next_kolo_instances = [kolo for kolo in future_kolos if kolo.date == next_date]

        # If there are less than 3 events on the next date, try to get one more recent event
        if len(next_kolo_instances) < 3:
            remaining_kolos = [kolo for kolo in future_kolos if kolo.date > next_date]
            if remaining_kolos:
                next_kolo_instances.append(remaining_kolos[0])


    event_data = []
    for kolo in next_kolo_instances:
        start_time = kolo.time.strftime('%H:%M')
        end_time = (datetime.combine(date.today(), kolo.time) + kolo.duration).time().strftime('%H:%M')
        polish_month = months[kolo.date.month - 1]

        event_data.append({
            'theme': kolo.theme,
            'date': f"{kolo.date.day} {polish_month} {kolo.date.year}",
            'time_range': f"{start_time} - {end_time}",
            'duration': kolo.duration,
            'tutors': kolo.tutors.all(),
            'description': kolo.description,
            'image': kolo.image,
            'file': kolo.file,
            'level': kolo.level,
            'finished': kolo.finished,
        })

    posts = Post.objects.all()
    reversed_posts = reversed(posts)

    context = {
        "posts": reversed_posts,
        "eventy": event_data,
        "user": request.user}

    return render(request, "index.html", context)


def about(request):
    return render(request, "about.html")

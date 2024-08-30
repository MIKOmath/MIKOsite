from django.shortcuts import render
from mainSite.models import Post
from kolomat.models import Kolo
from datetime import datetime, date
from babel.dates import format_date, format_time
from babel import Locale


# @cache_page(60*5)
def index(request):
    today = date.today()
    now = datetime.now().time()
    locale = Locale('pl_PL')

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
        start_time = format_time(kolo.time, format='HH:mm', locale=locale)
        end_time = format_time((datetime.combine(date.today(), kolo.time) + kolo.duration).time(), format='HH:mm',
                               locale=locale)
        polish_date = format_date(kolo.date, format='d MMMM y', locale=locale)

        event_data.append({
            'theme': kolo.theme,
            'date': polish_date,
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

    formatted_posts = []
    for post in posts:
        formatted_post = {
            'title': post.title,
            'subtitle': post.subtitle,
            'authors': post.authors.all(),
            'file': post.file,
            'images': post.images.all(),
            'text_field_1': post.text_field_1,
            'text_field_2': post.text_field_2,
            'date': format_date(post.date, format='d MMMM y', locale=locale) if post.date else '',
            'time': format_time(post.time, format='HH:mm', locale=locale) if post.time else '',
        }
        formatted_posts.append(formatted_post)
    formatted_posts = reversed(formatted_posts)
    context = {
        "posts": formatted_posts,
        "eventy": event_data,
        "user": request.user
    }
    return render(request, "index.html", context)


def about(request):
    return render(request, "about.html")


def roadmap(request):
    return render(request, "roadmap.html")

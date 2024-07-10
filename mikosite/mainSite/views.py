from django.shortcuts import render
from mainSite.models import Post
from django.http import HttpResponse

# Create your views here.


def index(request):

    posts = Post.objects.all()
    reversed_posts = reversed(posts)
    context = {"posts": reversed_posts}

    context["user"] = request.user
    return render(request, "index.html", context)


def about(request):

    return render(request, "about.html")

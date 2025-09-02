from django.urls import path
from . import views

urlpatterns = [
    path("kola/", views.informacje, name="informacje"),
    path("calendar/", views.calendar, name="calendar"),
]

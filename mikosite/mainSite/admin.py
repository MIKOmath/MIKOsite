from django.contrib import admin

from .models import RegistrationEvent, Image, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "time")
    search_fields = ("title", "subtitle", "content")
    ordering = ("-date", "-time")


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("id", "image")


@admin.register(RegistrationEvent)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "location",
        "date_begin",
        "date_end",
        "registration_begin",
        "registration_end",
    )
    search_fields = ("name", "location")
    list_filter = ("date_begin", "date_end", "registration_begin", "registration_end", "location")
    ordering = ("-registration_end", "-date_begin", "name")

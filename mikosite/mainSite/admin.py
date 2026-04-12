from django.contrib import admin
from rangefilter.filters import DateRangeFilterBuilder
from more_admin_filters import MultiSelectRelatedOnlyFilter

from .models import RegistrationEvent, Image, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    autocomplete_fields = ("authors",)
    list_display = (
        "title",
        "date",
        "author_list",
    )
    search_fields = (
        "title",
        "subtitle",
        "authors__username",
        "authors__last_name",
        "authors__email",
    )
    list_filter = (
        ("date", DateRangeFilterBuilder(title="date")),
        ("authors", MultiSelectRelatedOnlyFilter),
    )
    ordering = ("-date", "-time")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("authors")

    @admin.display(description="Authors")
    def author_list(self, obj):
        return ", ".join(obj.authors.values_list("username", flat=True)) or "-"


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

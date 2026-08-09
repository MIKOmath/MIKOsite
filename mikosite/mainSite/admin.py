from django.contrib import admin
from django.utils.html import format_html
from rangefilter.filters import DateRangeFilterBuilder
from more_admin_filters import MultiSelectRelatedOnlyFilter

from .models import RegistrationEvent, Image, Partner, Post


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


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_published", "url")
    list_editable = ("order", "is_published")
    search_fields = ("name",)
    list_filter = ("is_published",)
    ordering = ("order", "name")


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
    readonly_fields = ("image_preview",)
    fieldsets = (
        (None, {"fields": ("name", "location")}),
        ("Terminy", {"fields": ("date_begin", "date_end", "registration_begin", "registration_end")}),
        ("Zapisy", {"fields": ("registration_url",)}),
        ("Zdjęcie", {
            "fields": ("image", "image_preview"),
            "description": (
                "Kafelek na stronie głównej przycina zdjęcie do wysokości karty, "
                "od 170 px na telefonie do 208 px na monitorze."
            ),
        }),
    )

    @admin.display(description="Podgląd")
    def image_preview(self, obj):
        if not obj.image:
            return "Brak zdjęcia - kafelek użyje zdjęcia domyślnego."
        return format_html(
            '<img src="{}" style="max-width:320px;border-radius:8px"><br>{}x{} px, {} kB',
            obj.image.url, obj.image.width, obj.image.height, round(obj.image.size / 1024),
        )

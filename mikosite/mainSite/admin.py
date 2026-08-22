from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from rangefilter.filters import DateRangeFilterBuilder
from more_admin_filters import MultiSelectRelatedOnlyFilter

from .models import Badge, Bio, RegistrationEvent, Image, Partner, Post

# The admin never loads the site stylesheets, so a badge swatch repeats the
# brand colours as literals.
BADGE_SWATCHES = {
    Badge.Color.EXECUTIVE: ('#F24535', '#ffffff'),
    Badge.Color.NORMAL: ('#074A59', '#ffffff'),
    Badge.Color.AWARD: ('#F2B544', '#06313E'),
}


def render_image_preview(image, empty, width=320):
    if not image:
        return empty
    return format_html(
        '<img src="{}" style="max-width:{}px;border-radius:8px"><br>{}x{} px, {} kB',
        image.url, width, image.width, image.height, round(image.size / 1024),
    )


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
        "is_published",
    )
    list_editable = ("is_published",)
    search_fields = ("name", "location")
    list_filter = (
        "is_published",
        "date_begin",
        "date_end",
        "registration_begin",
        "registration_end",
        "location",
    )
    ordering = ("-registration_end", "-date_begin", "name")
    readonly_fields = ("image_preview",)
    fieldsets = (
        (None, {"fields": ("name", "location", "is_published")}),
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
        return render_image_preview(obj.image, "Brak zdjęcia - kafelek użyje zdjęcia domyślnego.")


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("text", "swatch", "color", "icon", "order", "bio_count")
    list_editable = ("color", "icon", "order")
    list_filter = ("color",)
    search_fields = ("text",)
    ordering = ("order", "text")
    fields = ("text", "color", "icon", "order")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(Count("bios"))

    @admin.display(description="Podgląd")
    def swatch(self, obj):
        background, colour = BADGE_SWATCHES[obj.color]
        return format_html(
            '<span style="display:inline-block;padding:4px 6px;border-radius:4px;'
            'font-size:14px;font-weight:bold;background:{};color:{}">{}</span>',
            background, colour, obj.text,
        )

    @admin.display(description="Wizytówki", ordering="bios__count")
    def bio_count(self, obj):
        return obj.bios__count


@admin.register(Bio)
class BioAdmin(admin.ModelAdmin):
    autocomplete_fields = ("user",)
    filter_horizontal = ("badges",)
    list_display = ("name", "order", "is_published", "badge_list")
    list_editable = ("order", "is_published")
    list_filter = ("is_published", "badges")
    search_fields = ("user__username", "user__first_name", "user__last_name", "description")
    ordering = ("order", "pk")
    readonly_fields = ("image_preview",)
    fieldsets = (
        (None, {
            "fields": ("user", "order", "is_published"),
            "description": (
                "Imię i nazwisko na wizytówce pochodzą z konta użytkownika - "
                "edytuj je w sekcji Użytkownicy."
            ),
        }),
        ("Treść", {"fields": ("description", "badges")}),
        ("Zdjęcie", {"fields": ("image", "image_preview")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user").prefetch_related("badges")

    @admin.display(description="Osoba", ordering="user__last_name")
    def name(self, obj):
        return str(obj)

    @admin.display(description="Plakietki")
    def badge_list(self, obj):
        return ", ".join(badge.text for badge in obj.badges.all()) or "-"

    @admin.display(description="Podgląd")
    def image_preview(self, obj):
        return render_image_preview(obj.image, "Brak zdjęcia - kafelek użyje ikony.", width=300)

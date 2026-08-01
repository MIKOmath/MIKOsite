import re
from datetime import datetime, timedelta

from django import forms
from django.contrib import admin
from django.utils.html import format_html
from rangefilter.filters import DateRangeFilterBuilder
from more_admin_filters import MultiSelectRelatedOnlyFilter

from .models import (
    DEFAULT_GROUP_COLOR,
    Seminar,
    SeminarGroup,
    GoogleFormsTemplate,
    PreviousEdition,
    PreviousEditionMilestone,
    Reminder,
)


COLOR_INPUT_ATTRS = {'placeholder': DEFAULT_GROUP_COLOR, 'size': 9, 'pattern': '#[0-9a-fA-F]{6}'}


class ColorFieldAdminMixin:
    """Shows the fallback colour as a placeholder so an empty field reads as "default"."""

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'color':
            kwargs['widget'] = forms.TextInput(attrs=COLOR_INPUT_ATTRS)
        return super().formfield_for_dbfield(db_field, request, **kwargs)


def color_swatch(color, label):
    return format_html(
        '<span style="display:inline-flex;align-items:center;gap:6px">'
        '<span style="width:14px;height:14px;border-radius:4px;border:1px solid rgba(0,0,0,.2);'
        'background:{}"></span>{}</span>',
        color,
        label,
    )


def theme_looks_fully_capitalized(theme):
    words = re.findall(r"[^\W\d_]+", theme, flags=re.UNICODE)
    if len(words) < 2:
        return False

    all_upper = all(word[0].isupper() for word in words)
    any_lower = any(word[1:].islower() for word in words[1:])

    return all_upper and any_lower


class SeminarAdminForm(forms.ModelForm):
    confirm_capitalized_theme = forms.BooleanField(
        required=False,
        label="Confirm capitalization",
        help_text="Zaznacz, jeśli pisownia tematu koła jest poprawna, aby zignorować wbudowaną regułę.",
    )

    class Meta:
        model = Seminar
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        theme = self.data.get("theme", "") if self.is_bound else ""
        if not theme_looks_fully_capitalized(theme):
            self.fields["confirm_capitalized_theme"].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        theme = cleaned_data.get("theme") or ""
        confirmed = cleaned_data.get("confirm_capitalized_theme")

        if theme_looks_fully_capitalized(theme) and not confirmed:
            self.add_error(
                "confirm_capitalized_theme",
                "Sprawdź pisownię tematu koła i ponownie zapisz zmiany.",
            )
            raise forms.ValidationError(
                "W języku polskim tylko pierwszy wyraz tytułu zapisujemy wielką literą. Sprawdź pisownię tematu koła."
            )

        return cleaned_data


class SeminarGroupAdmin(ColorFieldAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'calendar_label', 'lead', 'seminar_count')
    ordering = ('-default_difficulty',)

    @admin.display(description="Etykieta w kalendarzu")
    def calendar_label(self, obj):
        return color_swatch(obj.display_color, obj.display_short_label)


class SeminarAdmin(admin.ModelAdmin):
    form = SeminarAdminForm
    autocomplete_fields = ("tutors",)
    list_display = (
        "theme",
        "date",
        "group",
        "tutor_list",
    )
    list_filter = [
        ('date', DateRangeFilterBuilder(title='data',
                                        default_start=lambda r: datetime.now() - timedelta(days=30),
                                        default_end=lambda r: datetime.now() + timedelta(days=90))),
        ('group', MultiSelectRelatedOnlyFilter),
        ('tutors', MultiSelectRelatedOnlyFilter),
    ]
    search_fields = [
        "theme",
        "tutors__username",
        "tutors__last_name",
        "tutors__email",
    ]
    ordering = ('-date', '-time')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("tutors")

    @admin.display(description="Tutors")
    def tutor_list(self, obj):
        return ", ".join(obj.tutors.values_list("username", flat=True)) or "-"


class GoogleFormsTemplateAdmin(admin.ModelAdmin):
    list_display = ('name',)


class PreviousEditionMilestoneInline(admin.StackedInline):
    model = PreviousEditionMilestone
    extra = 1
    fields = (
        ('date', 'show_date'),
        ('material_icon', 'title'),
        'description',
        'link_url',
    )


class PreviousEditionAdmin(admin.ModelAdmin):
    list_display = (
        'school_year_label',
        'start_date',
        'end_date',
        'seminar_count',
        'milestone_count',
        'member_count_label',
        'has_brochure',
        'is_published',
    )
    list_filter = ('is_published',)
    readonly_fields = ('school_year_label', 'seminar_count')
    fields = (
        'start_date',
        'end_date',
        'school_year_label',
        'member_count',
        'member_count_is_estimate',
        'brochure',
        'seminar_count',
        'is_published',
    )
    inlines = (PreviousEditionMilestoneInline,)
    ordering = ('-start_date',)

    @admin.display(boolean=True, description='Brochure')
    def has_brochure(self, obj):
        return bool(obj.brochure)

    @admin.display(description='Milestones')
    def milestone_count(self, obj):
        return obj.milestones.count()


class ReminderAdmin(admin.ModelAdmin):
    list_filter = [
        ('date_time', DateRangeFilterBuilder(title='date',
                                             default_start=lambda r: datetime.now() - timedelta(days=7),
                                             default_end=lambda r: datetime.now() + timedelta(days=30))),
    ]
    list_display = ('type', 'date_time', 'seminar')
    ordering = ('date_time',)


admin.site.register(SeminarGroup, SeminarGroupAdmin)
admin.site.register(Seminar, SeminarAdmin)
admin.site.register(GoogleFormsTemplate, GoogleFormsTemplateAdmin)
admin.site.register(PreviousEdition, PreviousEditionAdmin)
admin.site.register(Reminder, ReminderAdmin)

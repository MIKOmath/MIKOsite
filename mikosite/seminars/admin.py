import re
from datetime import datetime, timedelta

from django import forms
from django.contrib import admin
from rangefilter.filters import DateRangeFilterBuilder
from more_admin_filters import MultiSelectRelatedOnlyFilter

from .models import Seminar, SeminarGroup, GoogleFormsTemplate, Reminder


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


class SeminarGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'lead', 'seminar_count')
    ordering = ('-default_difficulty',)


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
admin.site.register(Reminder, ReminderAdmin)

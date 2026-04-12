from datetime import datetime, timedelta
from django.contrib import admin
from .models import Seminar, SeminarGroup, GoogleFormsTemplate, Reminder
from rangefilter.filters import DateRangeFilterBuilder
from more_admin_filters import MultiSelectRelatedOnlyFilter


class SeminarGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'lead', 'seminar_count')
    ordering = ('-default_difficulty',)


class SeminarAdmin(admin.ModelAdmin):
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

from datetime import datetime, timedelta
from django.contrib import admin
from .models import Seminar, SeminarGroup, GoogleFormsTemplate, Reminder
from rangefilter.filters import DateRangeFilterBuilder
from more_admin_filters import MultiSelectRelatedOnlyFilter


class SeminarGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'lead', 'seminar_count')
    ordering = ('-default_difficulty',)


class SeminarAdmin(admin.ModelAdmin):
    list_filter = [
        ('date', DateRangeFilterBuilder(title='data',
                                        default_start=lambda r: datetime.now() - timedelta(days=7),
                                        default_end=lambda r: datetime.now() + timedelta(days=30))),
        ('group', MultiSelectRelatedOnlyFilter),
        ('tutors', MultiSelectRelatedOnlyFilter),
    ]
    search_fields = ['theme']
    ordering = ('-date', '-time')


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

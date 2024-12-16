from datetime import datetime, timedelta
from django.contrib import admin
from .models import Seminar, SeminarGroup
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


admin.site.register(SeminarGroup, SeminarGroupAdmin)
admin.site.register(Seminar, SeminarAdmin)

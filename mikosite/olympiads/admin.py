from django import forms
from django.contrib import admin
from rangefilter.filters import DateRangeFilterBuilder
from more_admin_filters import MultiSelectRelatedOnlyFilter

from .models import Olympiad, OlympiadStage


@admin.register(Olympiad)
class OlympiadAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'name', 'stage_count', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('name', 'short_name')
    ordering = ('order', 'name')

    @admin.display(description="Etapy")
    def stage_count(self, obj):
        return obj.stage_count


@admin.register(OlympiadStage)
class OlympiadStageAdmin(admin.ModelAdmin):
    list_display = ('olympiad', 'name', 'date_begin', 'date_end', 'location', 'is_published')
    list_editable = ('is_published',)
    list_filter = (
        'is_published',
        ('olympiad', MultiSelectRelatedOnlyFilter),
        ('date_begin', DateRangeFilterBuilder(title='data rozpoczęcia')),
    )
    search_fields = ('name', 'olympiad__name', 'olympiad__short_name')
    ordering = ('-date_begin',)
    autocomplete_fields = ('olympiad',)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'name':
            suggestions = ', '.join(f'„{name}”' for name in OlympiadStage.SUGGESTED_STAGE_NAMES)
            kwargs['widget'] = forms.TextInput(attrs={'placeholder': OlympiadStage.DEFAULT_STAGE_NAME})
            kwargs['help_text'] = f"Dowolna nazwa etapu. Typowe wartości: {suggestions}."
        return super().formfield_for_dbfield(db_field, request, **kwargs)

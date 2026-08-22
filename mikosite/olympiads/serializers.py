from rest_framework import serializers

from mikosite.api import ModelCleanMixin

from .models import Olympiad, OlympiadStage


class OlympiadSerializer(serializers.ModelSerializer):
    """Public shape. `order` and `is_active` are editorial controls: the
    queryset has already applied both by the time anyone reads this."""

    class Meta:
        model = Olympiad
        fields = ['id', 'name', 'short_name', 'logo', 'website_url']
        read_only_fields = fields


class AdminOlympiadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Olympiad
        fields = ['id', 'name', 'short_name', 'logo', 'website_url', 'order', 'is_active']


class OlympiadStageSerializer(serializers.ModelSerializer):
    """Public shape, and the one the calendar embeds.

    `kind` and `title` mirror the registration-event shape so the calendar grid
    draws both kinds of multi-day band with one renderer.
    """

    kind = serializers.SerializerMethodField()
    stage_label = serializers.CharField(source='name', read_only=True)
    title = serializers.SerializerMethodField()
    date_range = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    olympiad = OlympiadSerializer(read_only=True)

    class Meta:
        model = OlympiadStage
        fields = [
            'id',
            'kind',
            'stage_label',
            'title',
            'date_begin',
            'date_end',
            'date_range',
            'location',
            'url',
            'note',
            'olympiad',
        ]
        read_only_fields = fields

    def get_kind(self, stage) -> str:
        return 'olympiad'

    def get_title(self, stage) -> str:
        return f"{stage.olympiad.short_name} – {stage.name}"

    def get_date_range(self, stage) -> str:
        return stage.date_range_label()

    def get_url(self, stage) -> str:
        # A stage without its own link falls back to the olympiad's site.
        return stage.url or stage.olympiad.website_url


class AdminOlympiadStageSerializer(ModelCleanMixin, serializers.ModelSerializer):
    class Meta:
        model = OlympiadStage
        fields = [
            'id',
            'olympiad',
            'name',
            'date_begin',
            'date_end',
            'location',
            'url',
            'note',
            'is_published',
        ]

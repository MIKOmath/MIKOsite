from rest_framework import serializers

from mikosite.api import ModelCleanMixin

from .models import (
    GoogleFormsTemplate,
    PreviousEdition,
    PreviousEditionMilestone,
    Reminder,
    Seminar,
    SeminarGroup,
)


class SeminarGroupBadgeSerializer(serializers.ModelSerializer):
    """The group as it appears beside a seminar: enough to draw the chip."""

    short_label = serializers.CharField(source='display_short_label', read_only=True)
    color = serializers.CharField(source='display_color', read_only=True)

    class Meta:
        model = SeminarGroup
        fields = ['id', 'name', 'short_label', 'color']
        read_only_fields = fields


class SeminarGroupSerializer(SeminarGroupBadgeSerializer):
    class Meta(SeminarGroupBadgeSerializer.Meta):
        fields = SeminarGroupBadgeSerializer.Meta.fields + [
            'lead',
            'description',
            'default_difficulty',
            'discord_role_id',
            'discord_channel_id',
            'discord_voice_channel_id',
        ]
        read_only_fields = fields


class AdminSeminarGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeminarGroup
        fields = [
            'id',
            'name',
            'short_label',
            'color',
            'lead',
            'description',
            'default_difficulty',
            'discord_role_id',
            'discord_channel_id',
            'discord_voice_channel_id',
        ]


class SeminarSerializer(serializers.ModelSerializer):
    """Public shape, and the one the calendar embeds."""

    time = serializers.TimeField(format='%H:%M', read_only=True)
    time_label = serializers.CharField(read_only=True)
    tutors = serializers.SlugRelatedField('full_name', many=True, read_only=True)
    group = SeminarGroupBadgeSerializer(read_only=True)
    difficulty_label = serializers.CharField(read_only=True)
    difficulty_icon = serializers.CharField(read_only=True)

    discord_channel_id = serializers.CharField(
        source='real_discord_channel_id', allow_null=True, read_only=True,
    )
    discord_voice_channel_id = serializers.CharField(
        source='real_discord_voice_channel_id', allow_null=True, read_only=True,
    )
    group_role_id = serializers.CharField(
        source='group.discord_role_id', allow_null=True, read_only=True,
    )

    class Meta:
        model = Seminar
        fields = [
            'id',
            'date',
            'time',
            'time_label',
            'duration',
            'theme',
            'description',
            'image',
            'file',
            'started',
            'finished',
            'featured',
            'special_guest',
            'difficulty',
            'difficulty_label',
            'difficulty_icon',
            'tutors',
            'group',
            'discord_channel_id',
            'discord_voice_channel_id',
            'group_role_id',
        ]
        read_only_fields = fields


class AdminSeminarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seminar
        fields = [
            'id',
            'date',
            'time',
            'duration',
            'theme',
            'description',
            'image',
            'file',
            'started',
            'finished',
            'featured',
            'special_guest',
            'difficulty',
            'group',
            'form',
            'tutors',
            'discord_channel_id',
            'discord_voice_channel_id',
        ]


class GoogleFormSerializer(serializers.ModelSerializer):
    """Administrator plane only - these are internal registration templates."""

    class Meta:
        model = GoogleFormsTemplate
        fields = ['id', 'name', 'file']


class ReminderSerializer(serializers.ModelSerializer):
    """Administrator plane only - the bot's ping schedule."""

    class Meta:
        model = Reminder
        fields = ['id', 'seminar', 'type', 'date_time', 'pinged']


class PreviousEditionMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreviousEditionMilestone
        fields = ['id', 'date', 'show_date', 'title', 'description', 'material_icon', 'link_url']


class PreviousEditionSerializer(serializers.ModelSerializer):
    """Public shape: what an edition was, and its brochure."""

    school_year_label = serializers.CharField(read_only=True)
    member_count_label = serializers.CharField(read_only=True)
    brochure_url = serializers.FileField(source='brochure', read_only=True)

    class Meta:
        model = PreviousEdition
        fields = ['id', 'school_year_label', 'start_date', 'end_date', 'member_count_label', 'brochure_url']
        read_only_fields = fields


class AdminPreviousEditionSerializer(ModelCleanMixin, serializers.ModelSerializer):
    school_year_label = serializers.CharField(read_only=True)
    milestones = PreviousEditionMilestoneSerializer(many=True, read_only=True)
    seminar_count = serializers.SerializerMethodField()

    class Meta:
        model = PreviousEdition
        fields = [
            'id',
            'school_year_label',
            'start_date',
            'end_date',
            'member_count',
            'member_count_is_estimate',
            'brochure',
            'is_published',
            'seminar_count',
            'milestones',
        ]

    def get_seminar_count(self, edition) -> int:
        # Annotated by the viewset so a page of editions costs one query, not
        # one COUNT per row.
        if hasattr(edition, 'annotated_seminar_count'):
            return edition.annotated_seminar_count or 0
        return edition.seminar_count

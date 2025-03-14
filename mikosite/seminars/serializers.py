from rest_framework import serializers
from .models import SeminarGroup, Seminar, GoogleFormsTemplate, Reminder


class SeminarGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeminarGroup
        fields = '__all__'


class SeminarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seminar
        fields = '__all__'


class GoogleFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleFormsTemplate
        fields = '__all__'


class RemindersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = '__all__'


class DisplaySeminarSerializer(serializers.ModelSerializer):
    queryset = Seminar.objects.all().select_related('group').prefetch_related('tutors')
    tutors = serializers.SlugRelatedField('full_name', many=True, read_only=True)
    difficulty_label = serializers.CharField(read_only=True)
    difficulty_icon = serializers.CharField(read_only=True)
    group_name = serializers.CharField(source='group.name', allow_null=True, read_only=True)
    group_role_id = serializers.CharField(source='group.discord_role_id', allow_null=True, read_only=True)
    discord_channel_id = serializers.CharField(source='real_discord_channel_id', allow_null=True, read_only=True)
    discord_voice_channel_id = serializers.CharField(source='real_discord_voice_channel_id', allow_null=True, read_only=True)

    class Meta:
        model = Seminar
        fields = ['id', 'date', 'time', 'duration', 'group_name', 'theme', 'description', 'image', 'file',
                  'discord_channel_id','discord_voice_channel_id', 'group_role_id', 'started', 'finished', 'featured', 'special_guest',
                  'tutors', 'difficulty_label', 'difficulty_icon', 'form']

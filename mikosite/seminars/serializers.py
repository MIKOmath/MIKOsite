from rest_framework import serializers
from .models import SeminarGroup, Seminar

class SeminarGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeminarGroup
        fields = '__all__'


class SeminarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seminar
        fields = '__all__'


class DisplaySeminarSerializer(serializers.ModelSerializer):
    queryset = Seminar.objects.all().select_related('group').prefetch_related('tutors')
    tutors = serializers.SlugRelatedField('full_name', many=True, read_only=True)
    difficulty_label = serializers.CharField(read_only=True)
    group_name = serializers.CharField(source='group.name', allow_null=True, read_only=True)
    group_role_id = serializers.CharField(source='group.discord_role_id', allow_null=True, read_only=True)

    class Meta:
        model = Seminar
        fields = ['id', 'date', 'time', 'duration', 'group_name', 'theme', 'description', 'image', 'file',
                  'discord_channel_id', 'group_role_id', 'started', 'finished', 'featured', 'special_guest',
                  'tutors', 'difficulty_label']

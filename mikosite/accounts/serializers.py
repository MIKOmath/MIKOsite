from rest_framework import serializers
from .models import User, LinkedAccount, ActivityScore


class LinkedAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkedAccount
        fields = '__all__'


class NestedLinkedAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkedAccount
        fields = ['id', 'external_id', 'platform', 'timestamp']


class UserSerializer(serializers.ModelSerializer):
    linked_accounts = NestedLinkedAccountSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'surname', 'region', 'profile_image', 'linked_accounts']


class SafeUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'profile_image']


class ActivityScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityScore
        fields = '__all__'

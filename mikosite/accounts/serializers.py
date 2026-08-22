from rest_framework import serializers

from .models import ActivityScore, LinkedAccount, User


class PublicUserSerializer(serializers.ModelSerializer):
    """What anyone may learn about a member."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'profile_image']
        read_only_fields = fields


class OwnLinkedAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkedAccount
        fields = ['id', 'external_id', 'platform', 'timestamp']
        read_only_fields = fields


class LinkedAccountSerializer(serializers.ModelSerializer):
    """Administrator plane: the platform identity behind an account."""

    class Meta:
        model = LinkedAccount
        fields = ['id', 'user', 'external_id', 'platform', 'timestamp']


class OwnActivityScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityScore
        fields = ['id', 'change', 'reason', 'timestamp']
        read_only_fields = fields


class ActivityScoreSerializer(serializers.ModelSerializer):
    """Administrator plane: a score always names the member it belongs to."""

    class Meta:
        model = ActivityScore
        fields = ['id', 'user', 'change', 'reason', 'timestamp']


class ActivityScoreFieldsMixin(serializers.Serializer):
    """The running total, taken from the queryset annotation when there is one.

    Reading the model property instead would cost an aggregate per row.
    """

    activity_score = serializers.SerializerMethodField()

    def get_activity_score(self, user) -> int:
        if hasattr(user, 'annotated_activity_score'):
            return user.annotated_activity_score or 0
        return user.activity_score


class PrivateUserSerializer(ActivityScoreFieldsMixin, PublicUserSerializer):
    """A member's own record, and everything the API will say about them."""

    linked_accounts = OwnLinkedAccountSerializer(many=True, read_only=True)
    activity_scores = OwnActivityScoreSerializer(many=True, read_only=True)

    class Meta(PublicUserSerializer.Meta):
        fields = PublicUserSerializer.Meta.fields + [
            'email',
            'first_name',
            'last_name',
            'region',
            'date_of_birth',
            'date_joined',
            'activity_score',
            'activity_scores',
            'linked_accounts',
        ]
        read_only_fields = fields


class AdminUserSerializer(ActivityScoreFieldsMixin, serializers.ModelSerializer):
    """Administrator plane, and the only writable user shape."""

    full_name = serializers.CharField(read_only=True)
    linked_accounts = OwnLinkedAccountSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'full_name',
            'profile_image',
            'email',
            'first_name',
            'last_name',
            'region',
            'date_of_birth',
            'date_joined',
            'last_login',
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
            'activity_score',
            'linked_accounts',
        ]
        read_only_fields = [
            'id',
            'full_name',
            'date_joined',
            'last_login',
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
            'activity_score',
            'linked_accounts',
        ]

    def create(self, validated_data):
        """An account minted here has no password!"""

        user = super().create(validated_data)
        user.set_unusable_password()
        user.save(update_fields=['password'])
        return user


class UserActivitySerializer(ActivityScoreFieldsMixin, serializers.ModelSerializer):
    """A member's place in the activity ranking."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'activity_score']
        read_only_fields = fields

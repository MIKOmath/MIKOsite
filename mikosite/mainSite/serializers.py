from django.templatetags.static import static
from rest_framework import serializers

from accounts.serializers import PublicUserSerializer
from mikosite.api import ModelCleanMixin
from mikosite.dates import format_day_range

from .models import DEFAULT_EVENT_IMAGE, Image, Partner, Post, RegistrationEvent


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'image']


class PostSerializer(serializers.ModelSerializer):
    """Public shape: an announcement exactly as the site renders it."""

    authors = PublicUserSerializer(many=True, read_only=True)
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'subtitle', 'date', 'time', 'content', 'authors', 'file', 'images']
        read_only_fields = fields


class AdminPostSerializer(serializers.ModelSerializer):
    """Administrator plane; relations are ids here so the shape is writable."""

    class Meta:
        model = Post
        fields = ['id', 'title', 'subtitle', 'date', 'time', 'content', 'authors', 'file', 'images']


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ['id', 'name', 'logo', 'url']
        read_only_fields = fields


class AdminPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ['id', 'name', 'logo', 'url', 'order', 'is_published']


class RegistrationEventSerializer(serializers.ModelSerializer):
    kind = serializers.SerializerMethodField()
    title = serializers.CharField(source='name', read_only=True)
    date_range = serializers.SerializerMethodField()
    registration_range = serializers.SerializerMethodField()
    registration_open = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = RegistrationEvent
        fields = [
            'id',
            'kind',
            'name',
            'title',
            'location',
            'date_begin',
            'date_end',
            'date_range',
            'registration_begin',
            'registration_end',
            'registration_range',
            'registration_url',
            'registration_open',
            'image_url',
        ]
        read_only_fields = fields

    def get_kind(self, event) -> str:
        return 'registration_event'

    def get_date_range(self, event) -> str:
        return event.format_date_range()

    def get_registration_range(self, event) -> str:
        return format_day_range(event.registration_begin, event.registration_end)

    def get_registration_open(self, event) -> bool:
        # `today` travels in the context so a whole calendar payload is judged
        # against one date rather than re-reading the clock per row.
        return event.registration_is_open(today=self.context.get('today'))

    def get_image_url(self, event) -> str:
        return event.image.url if event.image else static(DEFAULT_EVENT_IMAGE)


class AdminRegistrationEventSerializer(ModelCleanMixin, serializers.ModelSerializer):
    class Meta:
        model = RegistrationEvent
        fields = [
            'id',
            'name',
            'location',
            'date_begin',
            'date_end',
            'registration_begin',
            'registration_end',
            'registration_url',
            'image',
            'is_published',
        ]

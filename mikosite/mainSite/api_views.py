from django_filters import rest_framework as filters
from django_filters import UnknownFieldBehavior
from rest_framework import viewsets

from mikosite.api import AdminPlaneMixin
from mikosite.permissions import IsAdminOrReadOnly

from .models import Badge, Bio, Partner, Post, RegistrationEvent
from .serializers import (
    AdminBadgeSerializer,
    AdminBioSerializer,
    AdminPartnerSerializer,
    AdminPostSerializer,
    AdminRegistrationEventSerializer,
    BadgeSerializer,
    BioSerializer,
    PartnerSerializer,
    PostSerializer,
    RegistrationEventSerializer,
)

# Images have no endpoint of their own: they reach the public embedded in the
# announcements that carry them, and are uploaded through the admin panel.


class PostFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name='date', lookup_expr='gte')
    end_date = filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = Post
        fields = []
        unknown_field_behavior = UnknownFieldBehavior.IGNORE


class PostViewSet(AdminPlaneMixin, viewsets.ModelViewSet):
    """Announcements."""

    queryset = Post.objects.prefetch_related('authors', 'images').order_by('-date', '-time')
    serializer_class = PostSerializer
    admin_serializer_class = AdminPostSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = PostFilter


class PartnerViewSet(AdminPlaneMixin, viewsets.ModelViewSet):
    """Partners shown on the home page."""

    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    admin_serializer_class = AdminPartnerSerializer
    permission_classes = (IsAdminOrReadOnly,)
    published_field = 'is_published'


class RegistrationEventFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name='date_end', lookup_expr='gte')
    end_date = filters.DateFilter(field_name='date_begin', lookup_expr='lte')

    class Meta:
        model = RegistrationEvent
        fields = []
        unknown_field_behavior = UnknownFieldBehavior.IGNORE


class RegistrationEventViewSet(AdminPlaneMixin, viewsets.ModelViewSet):
    """Events with registration."""

    queryset = RegistrationEvent.objects.order_by('date_begin', 'date_end', 'pk')
    serializer_class = RegistrationEventSerializer
    admin_serializer_class = AdminRegistrationEventSerializer
    permission_classes = (IsAdminOrReadOnly,)
    published_field = 'is_published'
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RegistrationEventFilter


class BadgeViewSet(AdminPlaneMixin, viewsets.ModelViewSet):
    """Badges the about-page cards share.

    No published switch: a badge is visible wherever a visible card wears it.
    """

    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    admin_serializer_class = AdminBadgeSerializer
    permission_classes = (IsAdminOrReadOnly,)


class BioViewSet(AdminPlaneMixin, viewsets.ModelViewSet):
    """Team cards on the about page."""

    queryset = Bio.objects.select_related('user').prefetch_related('badges')
    serializer_class = BioSerializer
    admin_serializer_class = AdminBioSerializer
    permission_classes = (IsAdminOrReadOnly,)
    published_field = 'is_published'

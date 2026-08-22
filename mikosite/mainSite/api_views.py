from django_filters import rest_framework as filters
from django_filters import UnknownFieldBehavior
from rest_framework import viewsets

from mikosite.api import AdminPlaneMixin
from mikosite.permissions import IsAdminOrReadOnly

from .models import Partner, Post, RegistrationEvent
from .serializers import (
    AdminPartnerSerializer,
    AdminPostSerializer,
    AdminRegistrationEventSerializer,
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

from django_filters import rest_framework as filters
from django_filters import UnknownFieldBehavior
from rest_framework import viewsets

from mikosite.api import AdminPlaneMixin
from mikosite.permissions import IsAdminOrReadOnly

from .models import Olympiad, OlympiadStage
from .serializers import (
    AdminOlympiadSerializer,
    AdminOlympiadStageSerializer,
    OlympiadSerializer,
    OlympiadStageSerializer,
)


class OlympiadViewSet(AdminPlaneMixin, viewsets.ModelViewSet):
    """Competitions whose stages appear in the calendar."""

    queryset = Olympiad.objects.all()
    serializer_class = OlympiadSerializer
    admin_serializer_class = AdminOlympiadSerializer
    permission_classes = (IsAdminOrReadOnly,)
    published_field = 'is_active'


class OlympiadStageFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name='date_end', lookup_expr='gte')
    end_date = filters.DateFilter(field_name='date_begin', lookup_expr='lte')

    class Meta:
        model = OlympiadStage
        fields = ['olympiad']
        unknown_field_behavior = UnknownFieldBehavior.IGNORE


class OlympiadStageViewSet(AdminPlaneMixin, viewsets.ModelViewSet):
    """Stages of olympiads."""

    queryset = OlympiadStage.objects.select_related('olympiad')
    serializer_class = OlympiadStageSerializer
    admin_serializer_class = AdminOlympiadStageSerializer
    permission_classes = (IsAdminOrReadOnly,)
    published_field = 'is_published'
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = OlympiadStageFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.on_admin_plane:
            # Switching off a whole olympiad has to take its stages with it,
            # otherwise the switch only works for the calendar.
            queryset = queryset.filter(olympiad__is_active=True)
        return queryset

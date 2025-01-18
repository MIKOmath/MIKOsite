from rest_framework import viewsets
from django_filters import rest_framework as filters
from django_filters import UnknownFieldBehavior

from babel import Locale

from .models import SeminarGroup, Seminar, GoogleFormsTemplate
from .serializers import SeminarGroupSerializer, SeminarSerializer, DisplaySeminarSerializer, GoogleFormSerializer

locale = Locale('pl_PL')


class SeminarGroupViewSet(viewsets.ModelViewSet):
    queryset = SeminarGroup.objects.all()
    serializer_class = SeminarGroupSerializer


class SeminarFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name='date', lookup_expr='gte')
    end_date = filters.DateFilter(field_name='date', lookup_expr='lte')
    unknown_field_behavior = UnknownFieldBehavior.IGNORE

    class Meta:
        model = Seminar
        fields = ['group', 'date']


class GoogleFormViewSet(viewsets.ModelViewSet):
    queryset = GoogleFormsTemplate.objects.all()
    serializer_class = GoogleFormSerializer


class SeminarViewSet(viewsets.ModelViewSet):
    queryset = Seminar.objects.all()
    serializer_class = SeminarSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = SeminarFilter

    def get_queryset(self):
        display_only = self.request.query_params.get('display_only', None)
        return Seminar.objects.select_related('group').prefetch_related('tutors') if display_only else self.queryset

    def get_serializer_class(self):
        if self.action not in ['list', 'retrieve']:
            return self.serializer_class
        display_only = self.request.query_params.get('display_only', None)
        return DisplaySeminarSerializer if display_only else self.serializer_class

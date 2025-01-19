from datetime import datetime

from rest_framework import viewsets
from django_filters import rest_framework as filters
from rest_framework import permissions
from django_filters import UnknownFieldBehavior
from babel import Locale

from .models import SeminarGroup, Seminar, GoogleFormsTemplate, Reminder
from .serializers import SeminarGroupSerializer, SeminarSerializer, DisplaySeminarSerializer, GoogleFormSerializer, \
    RemindersSerializer

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
    permission_classes = [permissions.IsAdminUser]


class ReminderViewSet(viewsets.ModelViewSet):
    queryset = Reminder.objects.all()
    serializer_class = RemindersSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        # Filter reminders with `date_time` greater than now and order by `date_time`
        only_next = self.request.query_params.get('only_next', None)
        if only_next:
            base_reminder = Reminder.objects.filter(date_time__gt=datetime.now()).order_by('date_time')[:1]
            if len(base_reminder) > 0:
                return Reminder.objects.filter(date_time__exact=base_reminder[0].date_time)
            return Reminder.objects.none()
        else:
            return Reminder.objects.all()


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

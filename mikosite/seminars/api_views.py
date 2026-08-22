from datetime import datetime

from django.db.models import Count, IntegerField, OuterRef, Subquery, Value
from django.utils import timezone
from django_filters import rest_framework as filters
from django_filters import UnknownFieldBehavior
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from mikosite.api import AdminPlaneMixin
from mikosite.permissions import IsAdmin, IsAdminOrReadOnly, is_admin

from .calendar_data import MAX_CALENDAR_RANGE_DAYS, build_calendar_payload, get_calendar_payload
from .models import (
    GoogleFormsTemplate,
    PreviousEdition,
    Reminder,
    Seminar,
    SeminarGroup,
)
from .serializers import (
    AdminPreviousEditionSerializer,
    AdminSeminarGroupSerializer,
    AdminSeminarSerializer,
    GoogleFormSerializer,
    PreviousEditionSerializer,
    ReminderSerializer,
    SeminarGroupSerializer,
    SeminarSerializer,
)


class SeminarGroupViewSet(AdminPlaneMixin, viewsets.ModelViewSet):
    """Groups that seminars belong to."""

    queryset = SeminarGroup.objects.all()
    serializer_class = SeminarGroupSerializer
    admin_serializer_class = AdminSeminarGroupSerializer
    permission_classes = (IsAdminOrReadOnly,)


class SeminarFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name='date', lookup_expr='gte')
    end_date = filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = Seminar
        fields = ['group', 'date']
        unknown_field_behavior = UnknownFieldBehavior.IGNORE


class SeminarViewSet(AdminPlaneMixin, viewsets.ModelViewSet):
    """Seminars."""

    queryset = (
        Seminar.objects.select_related('group').prefetch_related('tutors').order_by('date', 'time')
    )
    serializer_class = SeminarSerializer
    admin_serializer_class = AdminSeminarSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = SeminarFilter


class PreviousEditionViewSet(AdminPlaneMixin, viewsets.ModelViewSet):
    """Past editions."""

    queryset = PreviousEdition.objects.all()
    serializer_class = PreviousEditionSerializer
    admin_serializer_class = AdminPreviousEditionSerializer
    permission_classes = (IsAdminOrReadOnly,)
    published_field = 'is_published'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.on_admin_plane:
            return queryset
        seminars_in_range = (
            Seminar.objects
            .filter(date__gte=OuterRef('start_date'), date__lte=OuterRef('end_date'))
            .order_by()
            .values(grouper=Value(1))
            .annotate(total=Count('pk'))
            .values('total')
        )
        return queryset.prefetch_related('milestones').annotate(
            annotated_seminar_count=Subquery(seminars_in_range, output_field=IntegerField()),
        )


class GoogleFormViewSet(viewsets.ModelViewSet):
    """Registration form templates."""

    queryset = GoogleFormsTemplate.objects.all()
    serializer_class = GoogleFormSerializer
    permission_classes = (IsAdmin,)


class ReminderViewSet(viewsets.ModelViewSet):
    """Scheduled reminders for seminars."""

    queryset = Reminder.objects.all()
    serializer_class = ReminderSerializer
    permission_classes = (IsAdmin,)

    def get_queryset(self):
        if not self.request.query_params.get('only_next'):
            return self.queryset
        # Everything due at the next scheduled moment, so one ping fires for all
        # the seminars starting together.
        next_reminder = (
            Reminder.objects.filter(date_time__gt=timezone.now()).order_by('date_time').first()
        )
        if next_reminder is None:
            return Reminder.objects.none()
        return Reminder.objects.filter(date_time__exact=next_reminder.date_time)


class CalendarViewSet(ViewSet):
    """Everything drawn on the calendar for one date range."""

    permission_classes = (AllowAny,)

    @staticmethod
    def _parse_date(raw_value, field_name):
        try:
            return datetime.strptime(raw_value, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            raise ValidationError({field_name: "Podaj datę w formacie YYYY-MM-DD."})

    def list(self, request, *args, **kwargs):
        start_date = self._parse_date(request.query_params.get('start_date'), 'start_date')
        end_date = self._parse_date(request.query_params.get('end_date'), 'end_date')

        if end_date < start_date:
            raise ValidationError({'end_date': "Data końca nie może być wcześniejsza niż data początku."})
        if (end_date - start_date).days + 1 > MAX_CALENDAR_RANGE_DAYS:
            raise ValidationError(
                {'end_date': f"Zakres nie może być dłuższy niż {MAX_CALENDAR_RANGE_DAYS} dni."}
            )

        if is_admin(request):
            return Response(build_calendar_payload(start_date, end_date, include_unpublished=True))
        return Response(get_calendar_payload(start_date, end_date))

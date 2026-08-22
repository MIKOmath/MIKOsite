from datetime import datetime

from django.db.models import Count, IntegerField, OuterRef, Subquery, Value
from django.http import HttpResponse
from django.utils import timezone
from django.utils.cache import get_conditional_response, patch_vary_headers
from django.utils.http import quote_etag
from django_filters import rest_framework as filters
from django_filters import UnknownFieldBehavior
from rest_framework import renderers, viewsets
from rest_framework.decorators import action
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
from .timetable_image import (
    build_week_image,
    get_week_image,
    image_etag,
    offered_week_starts,
    week_image_filename,
    week_image_ttl,
    week_start_of,
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


def schedules_seminars(request) -> bool:
    """Whoever may put a seminar in the calendar in the first place."""
    user = getattr(request, 'user', None)
    if not (user and user.is_authenticated):
        return False
    return user.has_perm('seminars.add_seminar') or user.has_perm('seminars.change_seminar')


class PNGRenderer(renderers.BaseRenderer):
    """Only here so `Accept: image/png` negotiates; the view writes the bytes."""

    media_type = 'image/png'
    format = 'png'
    charset = None
    render_style = 'binary'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class CalendarViewSet(ViewSet):
    """Everything drawn on the calendar for one date range."""

    permission_classes = (AllowAny,)

    def finalize_response(self, request, response, *args, **kwargs):
        """A request for a PNG that fails still answers in JSON - only the
        successful path returns bytes."""
        if isinstance(response, Response) and isinstance(
            getattr(request, 'accepted_renderer', None), PNGRenderer
        ):
            request.accepted_renderer = renderers.JSONRenderer()
            request.accepted_media_type = renderers.JSONRenderer.media_type
        return super().finalize_response(request, response, *args, **kwargs)

    @staticmethod
    def _parse_date(raw_value, field_name):
        try:
            return datetime.strptime(raw_value, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            raise ValidationError({field_name: "Podaj datę w formacie YYYY-MM-DD."})

    def _resolve_week(self, request, raw_value):
        """The Monday asked for, and whether it is one the public may have."""
        day = self._parse_date(raw_value, 'week') if raw_value else timezone.localdate()
        week_start = week_start_of(day)
        offered = offered_week_starts()

        if week_start in offered:
            return week_start, True
        if schedules_seminars(request):
            return week_start, False
        raise ValidationError({'week': (
            "Obraz planu obejmuje tygodnie zaczynające się od "
            f"{offered[0].isoformat()} do {offered[-1].isoformat()}."
        )})

    @staticmethod
    def _image_response(request, png, raw_etag, week_start, *, shareable):
        response = HttpResponse(png, content_type='image/png')
        response['Content-Disposition'] = f'inline; filename="{week_image_filename(week_start)}"'
        response['ETag'] = quote_etag(raw_etag)
        response['Cache-Control'] = (
            f'public, max-age={week_image_ttl()}' if shareable else 'private, no-store'
        )
        # Callers are served different sheets, so no cache in front of this may
        # hand one caller's copy to the next.
        patch_vary_headers(response, ('Cookie', 'Authorization'))
        return get_conditional_response(request, etag=response['ETag'], response=response)

    @action(detail=False, url_path='image', renderer_classes=[PNGRenderer, renderers.JSONRenderer])
    def image(self, request, *args, **kwargs):
        """One week of the calendar as a PNG poster, sized for sharing.

        `?week=YYYY-MM-DD` names any day of the week wanted and is rounded down
        to its Monday; without it, the week we are in.
        """
        week_start, on_offer = self._resolve_week(request, request.query_params.get('week'))

        shareable = on_offer and not is_admin(request)
        if not shareable:
            png = build_week_image(week_start, include_unpublished=is_admin(request))
            return self._image_response(request, png, image_etag(png), week_start, shareable=False)

        png, etag = get_week_image(week_start)
        return self._image_response(request, png, etag, week_start, shareable=True)

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

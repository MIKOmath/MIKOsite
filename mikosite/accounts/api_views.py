import uuid

from django.db.models import Sum
from django_filters import rest_framework as filters
from django_filters import UnknownFieldBehavior
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from mikosite.api import AdminPlaneMixin
from mikosite.permissions import (
    IsAdmin,
    IsAdminOrAuthenticatedReadOnly,
    SelfDetailOrAdminPermission,
    UserAccessPermission,
    is_admin,
)

from allauth.socialaccount.models import SocialAccount

from .models import ActivityScore, User
from .serializers import (
    ActivityScoreSerializer,
    AdminUserSerializer,
    LinkedAccountSerializer,
    OwnActivityScoreSerializer,
    PrivateUserSerializer,
    PublicUserSerializer,
    UserActivitySerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """Member profiles."""

    serializer_class = PublicUserSerializer
    permission_classes = (UserAccessPermission,)

    def get_queryset(self):
        # `password` is deferred so a hash is never even loaded into memory.
        queryset = (
            User.objects.defer('password')
            .annotate(annotated_activity_score=Sum('activity_scores__change'))
        )
        if self._reading_own_record():
            return queryset.prefetch_related('socialaccount_set', 'activity_scores')
        if is_admin(self.request):
            return queryset.prefetch_related('socialaccount_set', 'groups', 'user_permissions')
        return queryset

    def _reading_own_record(self) -> bool:
        user = self.request.user
        if not user.is_authenticated:
            return False
        if self.action == 'me':
            return True
        if self.action != 'retrieve':
            return False
        try:
            return uuid.UUID(str(self.kwargs.get('pk'))) == user.pk
        except (TypeError, ValueError):
            return False

    def get_serializer_class(self):
        # Own record first: an administrator reading themselves is still a
        # member reading their own profile, and gets their scores with it.
        if self._reading_own_record():
            return PrivateUserSerializer
        if is_admin(self.request):
            return AdminUserSerializer
        return PublicUserSerializer

    @action(detail=False, methods=['get'])
    def me(self, request, *args, **kwargs):
        """The caller's own record."""
        instance = self.get_queryset().get(pk=request.user.pk)
        return Response(self.get_serializer(instance).data)


class LinkedAccountFilter(filters.FilterSet):
    external_id = filters.CharFilter(field_name='uid')
    platform = filters.CharFilter(field_name='provider')

    class Meta:
        model = SocialAccount
        fields = ['user']
        unknown_field_behavior = UnknownFieldBehavior.IGNORE


class LinkedAccountViewSet(viewsets.ModelViewSet):
    """Platform links, served straight from allauth's SocialAccount."""

    queryset = SocialAccount.objects.select_related('user')
    serializer_class = LinkedAccountSerializer
    permission_classes = (IsAdmin,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = LinkedAccountFilter


class ActivityScoreFilter(filters.FilterSet):
    start_timestamp = filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    end_timestamp = filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')

    class Meta:
        model = ActivityScore
        fields = ['user']
        unknown_field_behavior = UnknownFieldBehavior.IGNORE


class ActivityScoreViewSet(AdminPlaneMixin, viewsets.ModelViewSet):
    queryset = ActivityScore.objects.all()
    serializer_class = OwnActivityScoreSerializer
    admin_serializer_class = ActivityScoreSerializer
    permission_classes = (IsAdminOrAuthenticatedReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ActivityScoreFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.on_admin_plane:
            return queryset.select_related('user')
        return queryset.filter(user=self.request.user)


class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """Members ranked by activity total."""

    serializer_class = UserActivitySerializer
    permission_classes = (SelfDetailOrAdminPermission,)

    def get_queryset(self):
        queryset = (
            User.objects.only('id', 'username', 'first_name', 'last_name')
            .annotate(annotated_activity_score=Sum('activity_scores__change'))
        )
        if not is_admin(self.request):
            return queryset.filter(pk=self.request.user.pk)
        if self.action == 'list':
            # A ranking of members who have never scored is just a member list.
            queryset = queryset.filter(annotated_activity_score__isnull=False)
        return queryset.order_by('-annotated_activity_score', 'username')

    @action(detail=False, methods=['get'])
    def me(self, request, *args, **kwargs):
        """The caller's own standing."""
        instance = self.get_queryset().get(pk=request.user.pk)
        return Response(self.get_serializer(instance).data)

from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django_filters import rest_framework as filters
from django_filters import UnknownFieldBehavior

from .models import User, LinkedAccount, ActivityScore
from .serializers import UserSerializer, SafeUserSerializer, LinkedAccountSerializer, ActivityScoreSerializer

from mikosite.permissions import IsAdminUserOrDetailReadOnly


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().defer('password', 'date_of_birth')
    serializer_class = SafeUserSerializer
    permission_classes = (IsAdminUserOrDetailReadOnly,)

    def get_serializer_class(self):
        if self.request.user and self.request.user.is_staff:
            return UserSerializer
        return self.serializer_class


class LinkedAccountFilter(filters.FilterSet):
    unknown_field_behavior = UnknownFieldBehavior.IGNORE

    class Meta:
        model = LinkedAccount
        fields = ['user', 'external_id', 'platform']


class LinkedAccountViewSet(viewsets.ModelViewSet):
    queryset = LinkedAccount.objects.all()
    serializer_class = LinkedAccountSerializer
    permission_classes = (IsAdminUser,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = LinkedAccountFilter


class ActivityScoreFilter(filters.FilterSet):
    unknown_field_behavior = UnknownFieldBehavior.IGNORE
    start_timestamp = filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    end_timestamp = filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')

    class Meta:
        model = ActivityScore
        fields = ['user']


class ActivityScoreViewSet(viewsets.ModelViewSet):
    queryset = ActivityScore.objects.all()
    serializer_class = ActivityScoreSerializer
    permission_classes = (IsAdminUser,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ActivityScoreFilter


class UserActivityViewSet(GenericViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAdminUser,)

    def list(self, request):
        users_with_scores = (
            User.objects.all()
            .only('id', 'username', 'name', 'surname')
            .annotate(total_score=Sum('activity_scores__change'))
            .filter(total_score__isnull=False)
            .order_by('-total_score')
        )

        page = self.paginate_queryset(users_with_scores)
        if page is None:  # pagination is disabled in settings
            return Response({'detail': "Improper pagination settings."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        data = [{'id': user.id,
                 'username': user.username,
                 'full_name': user.full_name,
                 'total_score': user.total_score, }
                for user in page]
        return self.get_paginated_response(data)

    def retrieve(self, request, pk=None):
        try:
            user = self.get_object()
            return Response({
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'total_score': user.activity_score,
            })
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

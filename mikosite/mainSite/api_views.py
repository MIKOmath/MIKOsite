from rest_framework import viewsets
from django_filters import rest_framework as filters
from django_filters import UnknownFieldBehavior

from .models import Post, Image
from .serializers import PostSerializer, DisplayPostSerializer, PostImageSerializer


class PostImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = PostImageSerializer


class PostFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name='date', lookup_expr='gte')
    end_date = filters.DateFilter(field_name='date', lookup_expr='lte')
    unknown_field_behavior = UnknownFieldBehavior.IGNORE

    class Meta:
        model = Post
        fields = []


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = PostFilter

    def get_queryset(self):
        display_only = self.request.query_params.get('display_only', None)
        return Post.objects.all().prefetch_related('authors', 'images') if display_only else self.queryset

    def get_serializer_class(self):
        if self.action not in ['list', 'retrieve']:
            return self.serializer_class
        display_only = self.request.query_params.get('display_only', None)
        return DisplayPostSerializer if display_only else self.serializer_class

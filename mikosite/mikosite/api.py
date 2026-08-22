"""Shared viewset behaviour for the two access planes.

Every resource is served by one viewset with two serializers: a public shape
that carries only fields the site already shows the world, and an administrator
shape that carries the rest and is the only one that accepts writes. Rows an
administrator has switched off are invisible off the administrator plane.
"""
import copy

from mikosite.permissions import is_admin


class ModelCleanMixin:
    """Run the model's own `clean()` on the API path.

    DRF never calls `Model.clean()`, so rules like "an edition may not overlap
    another edition" or "a stage ends after it begins" held in the admin panel
    and silently did not hold over the API.
    """

    def validate(self, attrs):
        instance = copy.deepcopy(self.instance) if self.instance is not None else self.Meta.model()
        # A m2m field refuses direct assignment, and has no row to hang off
        # before the instance is saved, so `clean()` cannot see it either way.
        related = {field.name for field in self.Meta.model._meta.many_to_many}
        for field, value in attrs.items():
            if field not in related:
                setattr(instance, field, value)
        instance.clean()
        return attrs


class AdminPlaneMixin:
    """Pick the serializer and the queryset for the caller's plane.

    `serializer_class` is the public shape. `admin_serializer_class` is the
    administrator's; leaving it unset means the resource has no public shape at
    all and `permission_classes` is expected to say so. `published_field` names
    the boolean an administrator uses to hide a row from the public plane.
    """

    admin_serializer_class = None
    published_field = None

    @property
    def on_admin_plane(self) -> bool:
        return is_admin(self.request)

    def get_serializer_class(self):
        if self.on_admin_plane and self.admin_serializer_class is not None:
            return self.admin_serializer_class
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.published_field and not self.on_admin_plane:
            queryset = queryset.filter(**{self.published_field: True})
        return queryset

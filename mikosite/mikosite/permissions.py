"""The API's access planes.

There are exactly two: the public plane, which anonymous and signed-in members
share, and the administrator plane. `is_admin` is the single definition of an
administrator for the whole API - being staff grants access to the Django admin
panel and nothing else.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_admin(request) -> bool:
    user = getattr(request, 'user', None)
    return bool(user and user.is_authenticated and user.is_superuser)


class IsAdmin(BasePermission):
    """Administrator plane only. The project-wide default, so a viewset that
    forgets to declare its permissions is closed rather than open."""

    def has_permission(self, request, view):
        return is_admin(request)


class IsAdminOrReadOnly(BasePermission):
    """Anyone may read, only administrators may write."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or is_admin(request)


class IsAdminOrAuthenticatedReadOnly(BasePermission):
    """Signed-in members may read, only administrators may write."""

    def has_permission(self, request, view):
        if is_admin(request):
            return True
        user = getattr(request, 'user', None)
        return request.method in SAFE_METHODS and bool(user and user.is_authenticated)


class UserAccessPermission(BasePermission):
    """One member may be read by anyone, the member list only by administrators."""

    def has_permission(self, request, view):
        if is_admin(request):
            return True
        if view.action == 'me':
            user = getattr(request, 'user', None)
            return bool(user and user.is_authenticated)
        return view.action == 'retrieve'


class SelfDetailOrAdminPermission(BasePermission):
    """A member may read their own row; the listing is an administrator's.

    The viewset narrows the queryset to the caller, so asking for someone
    else's row is a 404 rather than a signal that it exists.
    """

    def has_permission(self, request, view):
        if is_admin(request):
            return True
        if view.action not in ('retrieve', 'me'):
            return False
        user = getattr(request, 'user', None)
        return bool(user and user.is_authenticated)

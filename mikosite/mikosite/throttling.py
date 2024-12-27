from rest_framework.throttling import UserRateThrottle
from rest_framework.authtoken.models import Token


class SessionUserThrottle(UserRateThrottle):
    scope = 'session_user'

    def get_cache_key(self, request, view):
        if request.user.is_authenticated and isinstance(request.auth, Token):
            return None
        return super().get_cache_key(request, view)

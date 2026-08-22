from functools import lru_cache

from django.conf import settings
from django.contrib.auth.password_validation import password_validators_help_texts


@lru_cache(maxsize=1)
def _pwd_help_texts():
    return password_validators_help_texts()


def turnstile_keys(request):
    """Settings the auth templates need: the Turnstile site key and the
    password rules for the aside card."""
    return {
        'turnstile_site_key': settings.TURNSTILE_SITE_KEY,
        'pwd_help_texts': _pwd_help_texts(),
    }

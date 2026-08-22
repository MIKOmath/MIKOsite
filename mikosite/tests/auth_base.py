"""Shared fixtures for the auth-flow tests. Not named test_*, so the runner
collects it as a helper rather than a suite."""
from unittest import mock

from accounts.models import User
from allauth.account.models import EmailAddress

PASSWORD = 'Correct1!horse'
NEW_PASSWORD = 'Different2@horse'

TURNSTILE_OK = mock.patch('accounts.signup_extras.verify_turnstile', return_value=(True, ''))
TURNSTILE_FAIL = mock.patch(
    'accounts.signup_extras.verify_turnstile',
    return_value=(False, "Potwierdź, że nie jesteś botem."),
)


def make_verified_user(username='marek123', email='marek@test.com', password=PASSWORD):
    user = User.objects.create_user(username=username, email=email, password=password)
    EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
    return user

"""Allauth form overrides: house widget styling, Turnstile on the two forms an
anonymous bot can drive into sending mail or creating accounts. Social flows
carry no Turnstile - the provider was the gate. The extra profile fields live
in signup_extras.py (imported by allauth, so it cannot import back into here).
"""
from allauth.account.forms import (
    ChangePasswordForm,
    LoginForm,
    ResetPasswordForm,
    ResetPasswordKeyForm,
    SetPasswordForm,
    SignupForm,
)

from .signup_extras import HouseWidgetsMixin, TurnstileFormMixin


class HouseLoginForm(HouseWidgetsMixin, LoginForm):
    pass


class TurnstileSignupForm(TurnstileFormMixin, SignupForm):
    turnstile_action = 'signup'


class HouseChangePasswordForm(HouseWidgetsMixin, ChangePasswordForm):
    pass


class HouseSetPasswordForm(HouseWidgetsMixin, SetPasswordForm):
    pass


class TurnstileResetPasswordForm(TurnstileFormMixin, HouseWidgetsMixin, ResetPasswordForm):
    turnstile_action = 'reset'


class HouseResetPasswordKeyForm(HouseWidgetsMixin, ResetPasswordKeyForm):
    pass

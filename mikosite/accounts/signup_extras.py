"""Signup-form building blocks that must not import allauth's forms:
ACCOUNT_SIGNUP_FORM_CLASS is imported while allauth.account.forms is still
initializing, so importing it back from here would be circular."""
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from allauth.core import context

from .models import REGION_CHOICES
from .turnstile import get_client_ip, verify_turnstile
from .validators import ValidateMinAge


class HouseWidgetsMixin:
    """Stamp the house CSS classes onto every widget, so templates can render
    bound fields directly."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.RadioSelect)):
                continue
            css = 'auth-select' if isinstance(widget, forms.Select) else 'auth-input'
            widget.attrs['class'] = f"{widget.attrs.get('class', '')} {css}".strip()


class TurnstileFormMixin:
    """Validate the Cloudflare token. Fail-closed: no secret configured means
    no submissions, the same stance the old signup view took."""

    turnstile_action = 'signup'

    def clean(self):
        cleaned_data = super().clean()
        request = context.request
        token = request.POST.get('cf-turnstile-response', '') if request else ''
        remote_ip = get_client_ip(request.META) if request else None
        ok, message = verify_turnstile(
            token=token,
            secret=settings.TURNSTILE_SECRET_KEY,
            remote_ip=remote_ip,
            expected_action=self.turnstile_action,
        )
        if not ok:
            raise ValidationError(message)
        return cleaned_data


class SignupExtrasForm(HouseWidgetsMixin, forms.Form):
    """Profile fields the User model requires beyond allauth's own. Mixed into
    local signup and social completion alike; the adapter saves the values."""

    first_name = forms.CharField(label="Imię", max_length=150)
    last_name = forms.CharField(label="Nazwisko", max_length=150)
    region = forms.ChoiceField(label="Województwo", choices=REGION_CHOICES)
    date_of_birth = forms.DateField(
        label="Data urodzenia",
        validators=[ValidateMinAge(settings.MIN_AGE_YEARS)],
        widget=forms.DateInput(attrs={'type': 'date', 'min': '1900-01-01'}),
    )

    def signup(self, request, user):
        """Required by allauth to exist, deliberately empty: it fires after the
        first save, too late for the NOT NULL date_of_birth - the adapter's
        save_user applies the fields instead."""

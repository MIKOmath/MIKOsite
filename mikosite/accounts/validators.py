from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.utils.translation import gettext_lazy as _


def validate_not_future_date(value):
    """
    Validates that the given date is not in the future.
    """
    if value > timezone.now().date():
        raise ValidationError(
            _("Date can't be in the future."),
            code='future_date'
        )


def validate_min_age_13(value):
    """
    Validates that the person with the given birth date is at least 13 years old.
    """
    today = timezone.now().date()
    
    age = relativedelta(today, value).years

    if age < 13:
        raise ValidationError(
            _('You must be at least 13 years old to register.'),
            code='min_age_violation'
        )


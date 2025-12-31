from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError


@deconstructible
class ValidateMinAge:
    message = _("Musisz mieć przynajmniej %(min_age)d lat, aby korzystać z tej strony.")

    def __init__(self, min_age):
        if not isinstance(min_age, int) or min_age < 0:
            raise ValueError("Minimum age must be a non-negative integer.")
        self.min_age = min_age

    def __call__(self, value):
        today = localdate()
        try:
            cutoff = value.replace(year=today.year - self.min_age)
        except ValueError:
            # handle February 29 for leap years
            cutoff = value.replace(year=today.year - self.min_age, day=value.day - 1)

        if value > cutoff:
            raise ValidationError(
                self.message,
                code='min_age',
                params={'min_age': self.min_age},
            )

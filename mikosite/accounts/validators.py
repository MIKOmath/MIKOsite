import string

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


class UpperDigitSpecialValidator:
    def __init__(self, min_upper=1, min_digits=1, min_special=1, special_chars=None):
        self.min_upper = int(min_upper)
        self.min_digits = int(min_digits)
        self.min_special = int(min_special)
        self.special_chars = special_chars or string.punctuation

    def validate(self, password, user=None):
        upper = sum(1 for c in password if c.isupper())
        digits = sum(1 for c in password if c.isdigit())
        special = sum(1 for c in password if c in self.special_chars)

        errors = []
        if upper < self.min_upper:
            errors.append(_("Hasło musi zawierać co najmniej %(n)s wielką literę.") % {"n": self.min_upper})
        if digits < self.min_digits:
            errors.append(_("Hasło musi zawierać co najmniej %(n)s cyfrę.") % {"n": self.min_digits})
        if special < self.min_special:
            errors.append(_("Hasło musi zawierać co najmniej %(n)s znak specjalny.") % {"n": self.min_special})

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Twoje hasło musi zawierać co najmniej %(u)s wielką literę, %(d)s cyfrę i %(s)s znak specjalny."
        ) % {"u": self.min_upper, "d": self.min_digits, "s": self.min_special}

from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models
from django.db.models import Q

from mikosite.dates import format_day_range


class Olympiad(models.Model):
    """A competition whose stages are shown as multi-day entries in the calendar."""

    name = models.CharField(max_length=128, unique=True, blank=False, null=False)
    short_name = models.CharField(
        max_length=32,
        blank=False,
        null=False,
        help_text="Skrót używany na pasku w kalendarzu, np. OM.",
    )
    logo = models.ImageField(
        upload_to='olympiad_logos/',
        blank=True,
        help_text="Logo wyświetlane przy etapach olimpiady w kalendarzu.",
    )
    website_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Strona olimpiady, używana dla etapów bez własnego odnośnika.",
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Kolejność wyświetlania w kalendarzu (rosnąco).",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Odznacz, aby ukryć etapy tej olimpiady w kalendarzu.",
    )

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "olimpiada"
        verbose_name_plural = "olimpiady"

    def __str__(self):
        return self.name

    @property
    def stage_count(self):
        return self.stages.count()



class OlympiadStage(models.Model):
    """A single, usually multi-day, stage of an olympiad in a given school year."""

    DEFAULT_STAGE_NAME = "II etap"
    SUGGESTED_STAGE_NAMES = ["II etap", "Finał"]

    olympiad = models.ForeignKey(Olympiad, on_delete=models.CASCADE, related_name='stages')
    name = models.CharField(
        max_length=64,
        default=DEFAULT_STAGE_NAME,
        help_text="Nazwa etapu wyświetlana w kalendarzu, np. „II etap” albo „Finał”.",
    )
    date_begin = models.DateField(blank=False, null=False)
    date_end = models.DateField(blank=False, null=False)
    location = models.CharField(max_length=128, blank=True)
    url = models.URLField(max_length=500, blank=True)
    note = models.CharField(max_length=256, blank=True)
    is_published = models.BooleanField(
        default=True,
        help_text="Odznacz, aby ukryć ten etap w kalendarzu i w API.",
    )

    class Meta:
        ordering = ['date_begin', 'olympiad__order', 'olympiad__name']
        verbose_name = "etap olimpiady"
        verbose_name_plural = "etapy olimpiad"
        constraints = [
            models.CheckConstraint(
                condition=Q(date_end__gte=models.F('date_begin')),
                name='olympiad_stage_end_after_begin',
            ),
            models.UniqueConstraint(
                fields=['olympiad', 'name', 'date_begin'],
                name='olympiad_stage_unique_per_start',
            ),
        ]
        indexes = [
            models.Index(fields=['date_begin', 'date_end']),
        ]

    def __str__(self):
        return f"{self.olympiad.short_name} {self.name} ({self.date_begin})"

    def clean(self):
        errors = {}

        if self.date_begin and self.date_end and self.date_end < self.date_begin:
            errors['date_end'] = "Data zakończenia etapu nie może być wcześniejsza niż data rozpoczęcia."

        if self.olympiad_id and self.date_begin and self.date_end:
            overlapping = OlympiadStage.objects.filter(
                olympiad_id=self.olympiad_id,
                name=self.name,
                date_begin__lte=self.date_end,
                date_end__gte=self.date_begin,
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                errors['date_begin'] = "Ten etap tej olimpiady już zajmuje wybrany zakres dat."

        if errors:
            raise ValidationError(errors)

    def date_range_label(self, locale=settings.BABEL_LOCALE) -> str:
        return format_day_range(self.date_begin, self.date_end, locale=locale)


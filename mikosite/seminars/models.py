from datetime import datetime
from babel.dates import format_date, format_time

from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
    URLValidator,
)
from django.conf import settings
from django.utils.safestring import mark_safe

from accounts.models import User


absolute_url_validator = URLValidator(schemes=["http", "https"])


class SeminarGroup(models.Model):
    name = models.CharField(max_length=256, blank=False, null=False)
    lead = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    discord_role_id = models.CharField(max_length=128, blank=True, null=True)
    discord_channel_id = models.CharField(max_length=128, blank=True, null=True)
    discord_voice_channel_id = models.CharField(max_length=128, blank=True, null=True)
    default_difficulty = models.IntegerField(default=0, blank=False, null=False,
                                             validators=[MinValueValidator(0), MaxValueValidator(5)])

    def __str__(self):
        return f"GROUP {self.name} LEVEL {self.default_difficulty}"

    @property
    def seminar_count(self):
        return self.seminar_set.count()

    def display_dict(self) -> dict:
        return {
            'lead': mark_safe(self.lead),
            'desc_snippets': [mark_safe(snippet) for snippet in self.description.split('\n')
                              if snippet and not snippet.isspace()],
        }


class GoogleFormsTemplate(models.Model):
    name = models.CharField(max_length=256, blank=False, null=False)
    file = models.FileField(upload_to='google_forms_templates/', blank=False, null=False)

    def __str__(self):
        return f"Form {self.name}"


class Seminar(models.Model):
    date = models.DateField(blank=False, null=False)
    time = models.TimeField(blank=False, null=False)
    duration = models.DurationField(blank=False, null=False)

    discord_channel_id = models.CharField(max_length=128, blank=True, null=True)
    discord_voice_channel_id = models.CharField(max_length=128, blank=True, null=True)
    started = models.BooleanField(default=False, blank=False, null=False)
    finished = models.BooleanField(default=False, blank=False, null=False)

    group = models.ForeignKey(SeminarGroup, on_delete=models.CASCADE, blank=True, null=True)
    form = models.ForeignKey(GoogleFormsTemplate, on_delete=models.SET_NULL, blank=True, null=True)
    difficulty = models.IntegerField(default=0, blank=False, null=False,
                                     validators=[MinValueValidator(0), MaxValueValidator(5)])

    featured = models.BooleanField(default=False, blank=False, null=False)
    special_guest = models.BooleanField(default=False, blank=False, null=False)

    tutors = models.ManyToManyField(User, blank=True)
    theme = models.CharField(max_length=256, blank=False, null=False)
    description = models.TextField(blank=True, null=True)

    image = models.ImageField(upload_to='kolo_images/', blank=True, null=True)
    file = models.FileField(upload_to='kolo_files/', blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["date", "time"]),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(started=True) | models.Q(finished=False),
                                   name="if_finished_then_started"),
        ]

    def __str__(self):
        return f"SEMINAR {self.theme} ON {self.date} AT {self.time}"

    difficulty_dict = {
        1: {'icon': 'signal_cellular_1_bar', 'label': 'początkujący'},
        2: {'icon': 'signal_cellular_2_bar', 'label': 'poziom średni'},
        3: {'icon': 'signal_cellular_3_bar', 'label': 'zaawansowany'},
        4: {'icon': 'signal_cellular_connected_no_internet_4_bar', 'label': 'olimpiady międzynarodowe'},
        5: {'icon': 'school', 'label': 'akademicki'},
    }

    @classmethod
    def fetch_upcoming(cls, start_timestamp: datetime = None):
        start_timestamp = start_timestamp or datetime.now()
        future_seminars = Seminar.objects.filter((Q(date=start_timestamp.date()) & Q(time__gt=start_timestamp.time()))
                                                 | Q(date__gt=start_timestamp.date()))
        future_seminars = future_seminars.order_by('date', 'time')

        first_seminar = future_seminars.first()
        if first_seminar is None:
            return []

        # get next 3 seminars or all that happen on the same (earliest) day
        next_seminars = future_seminars.filter(date=first_seminar.date)
        if next_seminars.count() < 3:
            next_seminars = future_seminars[:3]
        return next_seminars.select_related('group').prefetch_related('tutors')

    @property
    def start_timestamp(self):
        return datetime.combine(self.date, self.time)

    @property
    def end_timestamp(self):
        return datetime.combine(self.date, self.time) + self.duration

    @property
    def real_difficulty(self):
        default_difficulty = self.group.default_difficulty if self.group else None
        return self.difficulty or default_difficulty

    @property
    def real_discord_channel_id(self):
        default_channel = self.group.discord_channel_id if self.group else None
        return self.discord_channel_id or default_channel

    @property
    def real_discord_voice_channel_id(self):
        default_voice_channel = self.group.discord_voice_channel_id if self.group else None
        return self.discord_voice_channel_id or default_voice_channel

    @property
    def difficulty_label(self):
        return self.difficulty_dict.get(self.real_difficulty, {'label': None, 'icon': None})['label']

    @property
    def difficulty_icon(self):
        return self.difficulty_dict.get(self.real_difficulty, {'label': None, 'icon': None})['icon']

    def display_dict(self, locale=settings.BABEL_LOCALE) -> dict:
        polish_date = format_date(self.start_timestamp, format='d MMMM', locale=locale)
        start_time = format_time(self.start_timestamp, format='HH:mm', locale=locale)
        end_time = format_time(self.end_timestamp, format='HH:mm', locale=locale)

        difficulty_badge_content = self.difficulty_dict.get(self.real_difficulty, {'label': None, 'icon': None})

        return {
            'theme': self.theme,
            'description': self.description,
            'date_string': polish_date,
            'time_string': f"{start_time}-{end_time}",
            'tutors': [tutor.full_name for tutor in self.tutors.all()],
            'image_url': self.image.url if self.image else None,
            'file_url': self.file.url if self.file else None,
            'featured': self.featured,
            'special_guest': self.special_guest,
            'group_name': self.group.name if self.group else None,
            'difficulty_label': difficulty_badge_content['label'],
            'difficulty_icon': difficulty_badge_content['icon'],
        }


class PreviousEdition(models.Model):
    start_date = models.DateField(blank=False, null=False)
    end_date = models.DateField(blank=False, null=False)
    member_count = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Liczba członków na koniec edycji.",
    )
    member_count_is_estimate = models.BooleanField(
        default=True,
        help_text="Dodaje plus do liczby, np. 2000+.",
    )
    brochure = models.FileField(
        upload_to='brochures/',
        blank=True,
        validators=[FileExtensionValidator(['pdf'])],
        help_text="Opcjonalny plik PDF z materiałami dla tej edycji.",
    )
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-start_date']
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gte=models.F('start_date')),
                name='previous_edition_end_after_start',
            ),
        ]

    def __str__(self):
        return self.school_year_label

    def clean(self):
        errors = {}

        if self.start_date and self.end_date and self.end_date < self.start_date:
            errors['end_date'] = "Data końca edycji nie może być wcześniejsza niż data początku."

        if self.start_date and self.end_date:
            overlapping = PreviousEdition.objects.filter(
                start_date__lte=self.end_date,
                end_date__gte=self.start_date,
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                errors['start_date'] = "Zakres dat edycji nie może nachodzić na inną edycję."

        if errors:
            raise ValidationError(errors)

    @property
    def school_year_label(self):
        return f"Rok szkolny {self.start_date.year}/{str(self.end_date.year)[-2:]}"

    @property
    def seminar_count(self):
        return Seminar.objects.filter(date__gte=self.start_date, date__lte=self.end_date).count()

    @property
    def member_count_label(self):
        if self.member_count is None:
            return ""
        suffix = "+" if self.member_count_is_estimate else ""
        return f"{self.member_count}{suffix}"

    @property
    def brochure_url(self):
        return self.brochure.url if self.brochure else ""


class PreviousEditionMilestone(models.Model):
    edition = models.ForeignKey(
        PreviousEdition,
        on_delete=models.CASCADE,
        related_name='milestones',
    )
    date = models.DateField(blank=False, null=False)
    show_date = models.BooleanField(
        "Pokazuj datę",
        default=True,
        help_text="Odznacz, jeśli data ma być używana tylko do sortowania.",
    )
    title = models.CharField(max_length=200, blank=False, null=False)
    description = models.TextField(blank=True)
    material_icon = models.CharField(
        max_length=64,
        default='flag',
        help_text="Nazwa symbolu Material Icons, np. flag, emoji_events, school.",
    )
    link_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="Opcjonalny link. Dozwolone są pełne adresy http(s)://... oraz ścieżki w obrębie strony, np. /about/.",
    )

    class Meta:
        ordering = ['date', 'id']
        verbose_name = "kamień milowy"
        verbose_name_plural = "kamienie milowe"

    def __str__(self):
        return f"{self.edition.school_year_label}: {self.title}"

    def clean(self):
        errors = {}

        if self.edition_id and self.date:
            if self.date < self.edition.start_date or self.date > self.edition.end_date:
                errors['date'] = "Data kamienia milowego musi mieścić się w zakresie edycji."

        if self.link_url and not self.link_url.startswith('/'):
            try:
                absolute_url_validator(self.link_url)
            except ValidationError:
                errors['link_url'] = "Podaj pełny adres http(s)://... albo ścieżkę zaczynającą się od /."

        if errors:
            raise ValidationError(errors)


class Reminder(models.Model):
    seminar = models.ForeignKey(Seminar, on_delete=models.CASCADE, related_name='reminder')
    type = models.CharField(max_length=256, blank=False, null=False)
    date_time = models.DateTimeField()
    pinged = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(name='reminder_index', fields=['date_time'])]

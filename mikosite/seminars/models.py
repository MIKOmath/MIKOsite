from datetime import datetime, date
from babel.dates import format_date, format_time
from django.db import models
from django.db.models import Q
from django.core.validators import MaxValueValidator, MinValueValidator
from django.conf import settings
from django.utils.safestring import mark_safe

from accounts.models import User


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
    form = models.ForeignKey(GoogleFormsTemplate, blank=True, null=True)
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

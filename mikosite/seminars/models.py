from datetime import datetime, date
from babel.dates import format_date, format_time
from django.db import models
from accounts.models import User


class SeminarGroup(models.Model):
    name = models.CharField(max_length=256, blank=False, null=False)
    lead = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    default_difficulty = models.IntegerField(blank=True, null=True)
    discord_role_id = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return f"Group: {self.name} level {self.default_difficulty}"


class Seminar(models.Model):
    date = models.DateField(blank=True, null=True)
    time = models.TimeField(blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)

    discord_channel_id = models.CharField(max_length=128, blank=True, null=True)
    started = models.BooleanField(default=False, blank=True, null=True)
    finished = models.BooleanField(default=False, blank=True, null=True)

    group = models.ForeignKey(SeminarGroup, on_delete=models.CASCADE, blank=True, null=True)
    difficulty = models.IntegerField(blank=True, null=True)

    featured = models.BooleanField(default=False, blank=True, null=True)
    special_guest = models.BooleanField(default=False, blank=True, null=True)

    tutors = models.ManyToManyField(User, blank=True)
    theme = models.CharField(max_length=256, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    image = models.ImageField(upload_to='kolo_images/', blank=True, null=True)
    file = models.FileField(upload_to='kolo_files/', blank=True, null=True)


    def __str__(self):
        return f"Seminar: {self.theme} on {self.date} at {self.time}"

    def display_dict(self, locale) -> dict:
        start_time = format_time(self.time, format='HH:mm', locale=locale)
        end_time = format_time((datetime.combine(date.today(), self.time) + self.duration).time(),
                               format='HH:mm', locale=locale)
        polish_date = format_date(self.date, format='d MMMM', locale=locale)

        difficulty_dict = {
            1: {'icon': 'signal_cellular_1_bar', 'label': 'początkujący'},
            2: {'icon': 'signal_cellular_2_bar', 'label': 'poziom średni'},
            3: {'icon': 'signal_cellular_3_bar', 'label': 'zaawansowany'},
            4: {'icon': 'signal_cellular_connected_no_internet_4_bar', 'label': 'olimpiady międzynarodowe'},
            5: {'icon': 'school', 'label': 'akademicki'},
        }

        default_difficulty = self.group.default_difficulty if self.group else None
        difficulty_badge_content = difficulty_dict.get(self.difficulty or default_difficulty,
                                                       {'label': None, 'icon': None})
        return {
            'theme': self.theme,
            'description': self.description,
            'date_string': polish_date,
            'time_string': f"{start_time}-{end_time}",
            'tutors': [f'{tutor.name} {tutor.surname}' for tutor in self.tutors.all()],
            'image_url': self.image.url if self.image else None,
            'file_url': self.file.url if self.file else None,
            'featured': self.featured,
            'special_guest': self.special_guest,
            'group_name': self.group.name if self.group else None,
            'difficulty_label': difficulty_badge_content['label'],
            'difficulty_icon': difficulty_badge_content['icon'],
        }

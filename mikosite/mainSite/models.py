import os

from babel.dates import format_date, format_time
from markdown import Markdown

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe

from accounts.models import User
from mainSite.markdown import DisallowHeadersExtension
from mikosite.dates import format_day_range

md = Markdown(extensions=[DisallowHeadersExtension()])


class Post(models.Model):
    title = models.CharField(max_length=200, blank=False, null=False)
    subtitle = models.CharField(max_length=500, blank=True)
    date = models.DateField(blank=False, null=False)
    time = models.TimeField(blank=False, null=False)
    authors = models.ManyToManyField(User, blank=False)

    content = models.TextField(max_length=5000, blank=True)

    file = models.FileField(upload_to='post_files/', blank=True)
    images = models.ManyToManyField('Image', blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["date", "time"]),
        ]

    def __str__(self):
        return f"POST {self.title} PUBLISHED {self.date} {self.time}"

    def display_dict(self, locale=settings.BABEL_LOCALE) -> dict:
        return {
            'title': self.title,
            'subtitle': self.subtitle,
            'authors': [{'username': author.username, 'full_name': author.full_name} for author in self.authors.all()],
            'file': {'url': self.file.url, 'name': os.path.basename(self.file.name)} if self.file else {},
            'images': [{'url': image, 'alt_text': 'obraz do posta'} for image in self.images.all()],
            'content': mark_safe(md.convert(self.content)),
            'date': format_date(self.date, format='d MMMM y', locale=locale) if self.date else '',
            'time': format_time(self.time, format='HH:mm', locale=locale) if self.time else '',
        }


class Image(models.Model):
    image = models.ImageField(upload_to='post_images/', blank=True)

    def __str__(self):
        return str(self.image)


class RegistrationEvent(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=100)
    date_begin = models.DateField()
    date_end = models.DateField()
    registration_begin = models.DateField()
    registration_end = models.DateField()
    registration_url = models.URLField(max_length=500)

    def __str__(self):
        return f"{self.name} ({self.date_begin} - {self.date_end})"

    def clean(self):
        errors = {}

        if self.date_end < self.date_begin:
            errors["date_end"] = "Data zakończenia wydarzenia nie może być wcześniejsza niż data rozpoczęcia."

        if self.registration_end < self.registration_begin:
            errors["registration_end"] = "Data końca rejestracji nie może być wcześniejsza niż data początku rejestracji."

        if errors:
            raise ValidationError(errors)

    def format_date_range(self, locale=settings.BABEL_LOCALE) -> str:
        return format_day_range(self.date_begin, self.date_end, locale=locale)

    def registration_is_open(self, today=None) -> bool:
        today = today or timezone.localdate()
        return self.registration_begin <= today <= self.registration_end

    def display_dict(self, locale=settings.BABEL_LOCALE) -> dict:
        return {
            "name": self.name,
            "location": self.location,
            "date_range": self.format_date_range(locale=locale),
            "registration_link": self.registration_url,
        }

    def calendar_dict(self, today=None, locale=settings.BABEL_LOCALE) -> dict:
        return {
            "id": self.pk,
            "kind": "registration_event",
            "title": self.name,
            "location": self.location,
            "date_begin": self.date_begin.isoformat(),
            "date_end": self.date_end.isoformat(),
            "date_range": self.format_date_range(locale=locale),
            "registration_url": self.registration_url,
            "registration_open": self.registration_is_open(today=today),
            "registration_range": format_day_range(
                self.registration_begin, self.registration_end, locale=locale
            ),
        }

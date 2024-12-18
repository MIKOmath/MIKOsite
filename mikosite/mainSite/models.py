from babel.dates import format_date, format_time
from markdown import Markdown
from django.db import models
from django.utils.safestring import mark_safe

from accounts.models import User
from mainSite.markdown import DisallowHeadersExtension


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
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"POST {self.title} PUBLISHED {self.date} {self.time}"

    def display_dict(self, locale) -> dict:
        return {
            'title': self.title,
            'subtitle': self.subtitle,
            'authors': self.authors.all(),
            'file': self.file,
            'images': self.images.all(),
            'content': mark_safe(md.convert(self.content)),
            'date': format_date(self.date, format='d MMMM y', locale=locale) if self.date else '',
            'time': format_time(self.time, format='HH:mm', locale=locale) if self.time else '',
        }


class Image(models.Model):
    image = models.ImageField(upload_to='post_images/', blank=True)

    def __str__(self):
        return str(self.image)

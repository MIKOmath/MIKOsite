from django.db import models
from accounts.models import User
from babel.dates import format_date, format_time


class Post(models.Model):
    title = models.CharField(max_length=200, blank=False, null=False)
    subtitle = models.CharField(max_length=500, blank=True, null=True)
    date = models.DateField(blank=False, null=False)
    time = models.TimeField(blank=False, null=False)
    authors = models.ManyToManyField(User, blank=False)

    text_field_1 = models.TextField(max_length=5000, blank=True)
    text_field_2 = models.TextField(max_length=5000, blank=True)

    file = models.FileField(upload_to='post_files/', blank=True)
    images = models.ManyToManyField('Image', blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"Post: {self.title}"

    def display_dict(self, locale) -> dict:
        return {
            'title': self.title,
            'subtitle': self.subtitle,
            'authors': self.authors.all(),
            'file': self.file,
            'images': self.images.all(),
            'text_field_1': self.text_field_1,
            'text_field_2': self.text_field_2,
            'date': format_date(self.date, format='d MMMM y', locale=locale) if self.date else '',
            'time': format_time(self.time, format='HH:mm', locale=locale) if self.time else '',
        }


class Image(models.Model):
    image = models.ImageField(upload_to='post_images/', blank=True)

    def __str__(self):
        return str(self.image)

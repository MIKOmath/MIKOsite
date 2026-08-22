import os
from collections import namedtuple

from babel.dates import format_date, format_time
from markdown import Markdown

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.templatetags.static import static
from django.utils import timezone
from django.utils.safestring import mark_safe

from accounts.models import User
from mainSite.markdown import DisallowHeadersExtension
from mikosite.dates import format_day_range
from mikosite.images import ConvertedImageMixin

md = Markdown(extensions=[DisallowHeadersExtension()])

# Used when an event has no image of its own.
DEFAULT_EVENT_IMAGE = 'MIKO_GATHERING.webp'

# Twice the 300x200 the about page draws a card's photo at.
BIO_IMAGE_SIZE = getattr(settings, 'BIO_IMAGE_SIZE', (600, 400))


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


class Partner(models.Model):
    name = models.CharField(max_length=200, help_text="Nazwa widoczna dla czytników ekranu.")
    logo = models.ImageField(upload_to='partners/')
    url = models.URLField(max_length=500, blank=True, help_text="Opcjonalny link do strony partnera.")
    order = models.PositiveIntegerField(default=0, help_text="Mniejsza wartość - wcześniej na liście.")
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "partner"
        verbose_name_plural = "partnerzy"

    def __str__(self):
        return self.name

    def display_dict(self) -> dict:
        return {
            'name': self.name,
            'logo_url': self.logo.url if self.logo else '',
            'url': self.url,
        }


class RegistrationEvent(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=100)
    date_begin = models.DateField()
    date_end = models.DateField()
    registration_begin = models.DateField()
    registration_end = models.DateField()
    registration_url = models.URLField(max_length=500)
    is_published = models.BooleanField(
        default=True,
        help_text="Odznacz, aby ukryć wydarzenie w kalendarzu i w API.",
    )
    image = models.ImageField(
        upload_to='events/',
        blank=True,
        verbose_name="zdjęcie",
        help_text=(
            "Format WebP. Proporcje 16:9 (np. 1600×900 px), minimum 1200×675 px, "
            "do 400 kB. Kadr wypełnia całą szerokość kafelka, więc najważniejsze "
            "elementy trzymaj z dala od krawędzi. Puste pole = zdjęcie domyślne."
        ),
    )

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
            "image_url": self.image.url if self.image else static(DEFAULT_EVENT_IMAGE),
        }


# What each badge colour starts with, and the class badges.css paints it with.
BadgeStyle = namedtuple('BadgeStyle', 'icon css_class')


class Badge(models.Model):
    """A tag on an about-page card, shared between the people who wear it."""

    class Color(models.TextChoices):
        EXECUTIVE = 'executive', "zarząd"
        NORMAL = 'normal', "zwykła"
        AWARD = 'award', "osiągnięcie"

    STYLES = {
        Color.EXECUTIVE: BadgeStyle('badge', 'badge-featured'),
        Color.NORMAL: BadgeStyle('co_present', 'badge-light'),
        Color.AWARD: BadgeStyle('workspace_premium', 'badge-yellow'),
    }

    text = models.CharField(max_length=60, unique=True, verbose_name="napis")
    color = models.CharField(
        max_length=16,
        choices=Color.choices,
        default=Color.NORMAL,
        verbose_name="kolor",
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="ikona",
        help_text="Nazwa ikony Material Symbols. Puste pole = ikona domyślna dla koloru.",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="kolejność",
        help_text="Mniejsza wartość - wcześniej, na każdej wizytówce tak samo.",
    )

    class Meta:
        ordering = ['order', 'text']
        verbose_name = "plakietka"
        verbose_name_plural = "plakietki"

    def __str__(self):
        return self.text

    @property
    def css_class(self) -> str:
        return self.STYLES[self.color].css_class

    def save(self, *args, **kwargs):
        if not self.icon:
            self.icon = self.STYLES[self.color].icon
        super().save(*args, **kwargs)

    def display_dict(self) -> dict:
        return {'text': self.text, 'icon': self.icon, 'css_class': self.css_class}


class Bio(ConvertedImageMixin, models.Model):
    """One card in the about page's team grid."""

    IMAGE_SIZE = BIO_IMAGE_SIZE

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='bio',
        verbose_name="użytkownik",
        help_text="Imię i nazwisko na wizytówce pochodzą z tego konta.",
    )
    description = models.TextField(max_length=1000, verbose_name="opis")
    image = models.ImageField(
        upload_to='bios/',
        blank=True,
        verbose_name="zdjęcie",
        help_text=(
            "Dowolny format i rozmiar - zdjęcie zostanie przekonwertowane na WebP "
            f"i przycięte do {BIO_IMAGE_SIZE[0]}x{BIO_IMAGE_SIZE[1]} px. "
            "Puste pole = ikona zamiast portretu."
        ),
    )
    badges = models.ManyToManyField(
        Badge, blank=True, related_name='bios', verbose_name="plakietki",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="kolejność",
        help_text="Mniejsza wartość - wcześniej na stronie.",
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name="opublikowana",
        help_text="Odznacz, aby ukryć wizytówkę na stronie „Kim jesteśmy?”.",
    )

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = "wizytówka"
        verbose_name_plural = "wizytówki"

    def __str__(self):
        return self.name or self.user.username

    @property
    def name(self) -> str:
        return self.user.full_name.strip()

    @property
    def image_url(self) -> str:
        return self.image.url if self.image else ''

    def clean(self):
        # Not keyed on a field: the changelist form has no `user` to attach it to.
        if self.is_published and self.user_id and not self.name:
            raise ValidationError(
                "To konto nie ma imienia ani nazwiska, więc wizytówka byłaby bez podpisu."
            )

    def display_dict(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'image_url': self.image_url,
            'badges': [badge.display_dict() for badge in self.badges.all()],
        }

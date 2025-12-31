import uuid
from io import BytesIO

from PIL import Image, ImageOps

from django.db import models
from django.db.models import Q, Sum, CheckConstraint
from django.db.models.functions import Length
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, BaseUserManager

from .validators import ValidateMinAge

models.CharField.register_lookup(Length)

REGION_CHOICES = [
    ("DS", "dolnośląskie"),
    ("KP", "kujawsko-pomorskie"),
    ("LU", "lubelskie"),
    ("LB", "lubuskie"),
    ("LD", "łódzkie"),
    ("MA", "małopolskie"),
    ("MZ", "mazowieckie"),
    ("OP", "opolskie"),
    ("PK", "podkarpackie"),
    ("PD", "podlaskie"),
    ("PM", "pomorskie"),
    ("SL", "śląskie"),
    ("SK", "świętokrzyskie"),
    ("WN", "warmińsko-mazurskie"),
    ("WP", "wielkopolskie"),
    ("ZP", "zachodniopomorskie"),
    ('NA', 'nieznany'),
]

PROFILE_IMAGE_SIZE = getattr(settings, 'PROFILE_IMAGE_SIZE', (320, 320))
PROFILE_WEBP_QUALITY = 85


class MikoUserManager(BaseUserManager):
    def create_user(self, username, email, password, **extra_fields):
        if not email:
            raise ValueError(_("The email must be set."))
        email = self.normalize_email(email)

        extra_fields.setdefault('date_of_birth', timezone.localdate())
        extra_fields.setdefault('region', 'NA')
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    id = models.UUIDField(
        primary_key=True,
        verbose_name=_("Unique User ID"),
        default=uuid.uuid4,
        editable=False,
    )
    email = models.EmailField(
        verbose_name=_("Email Address"),
        unique=True,
        blank=False,
        null=False,
    )
    region = models.CharField(
        verbose_name=_("Region"),
        max_length=2,
        choices=REGION_CHOICES,
        blank=False,
        null=False,
    )
    date_of_birth = models.DateField(
        verbose_name=_("Date of Birth"),
        validators=[ValidateMinAge(getattr(settings, 'MIN_AGE_YEARS', 13))],
        blank=False,
        null=False,
    )
    profile_image = models.ImageField(
        verbose_name=_("Profile Image"),
        upload_to='profile_images/',
        blank=True,
        null=True,
    )

    objects = MikoUserManager()

    def __str__(self):
        return f"{self.username} ({self.first_name} {self.last_name})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def activity_score(self):
        return self.activity_scores.aggregate(Sum('change'))['change__sum'] or 0

    def _convert_profile_picture(self, file):
        img = Image.open(file)
        img = ImageOps.exif_transpose(img)

        if img.mode != 'RGB':
            img = img.convert('RGB')

        img = ImageOps.fit(img, PROFILE_IMAGE_SIZE, method=Image.LANCZOS)
        out = BytesIO()
        img.save(out, format='WEBP', quality=PROFILE_WEBP_QUALITY)
        out.seek(0)

        filename = f"{uuid.uuid4().hex}.webp"
        return ContentFile(out.read(), name=filename)

    def save(self, *args, **kwargs):
        old_picture_file = None
        if self.pk:
            try:
                old = type(self).objects.only('profile_image').get(pk=self.pk)
                old_picture_file = old.profile_image.name if old.profile_image else None
            except type(self).DoesNotExist:
                pass

        new_picture_file = getattr(self.profile_image, 'name', None)
        picture_changed = new_picture_file != old_picture_file

        if self.profile_image and picture_changed:
            self.profile_image = self._convert_profile_picture(self.profile_image)

        super().save(*args, **kwargs)

        if picture_changed and old_picture_file:
            storage = self.profile_image.storage
            if storage.exists(old_picture_file):
                storage.delete(old_picture_file)

    class Meta:
        constraints = [
            CheckConstraint(
                check=Q(username__length__gte=settings.MIN_USERNAME_LENGTH),
                violation_error_message=_(f'Nazwa użytkownika jest za krótka. Wymagana liczba znaków: {settings.MIN_USERNAME_LENGTH}.'),
                name='username_min_length',
            ),
            CheckConstraint(
                check=Q(username__length__lte=settings.MAX_USERNAME_LENGTH),
                violation_error_message=_(f'Nazwa użytkownika jest za długa. Dopuszczalna liczba znaków: {settings.MAX_USERNAME_LENGTH}.'),
                name='username_max_length',
            ),
        ]


class LinkedAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, related_name='linked_accounts', on_delete=models.CASCADE)
    external_id = models.CharField(max_length=128, blank=False, null=False)
    platform = models.CharField(max_length=50, blank=False, null=False)
    timestamp = models.DateTimeField(auto_now=True, blank=False, null=False)

    class Meta:
        unique_together = (('external_id', 'platform'), ('user', 'platform'))

    def __str__(self):
        return f"USER {self.user.username} IS {self.external_id} ON {self.platform}"


class ActivityScore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, related_name='activity_scores', on_delete=models.CASCADE)
    change = models.IntegerField(blank=False, null=False)
    reason = models.CharField(max_length=255, blank=False, null=False)
    timestamp = models.DateTimeField(default=timezone.now, blank=False, null=False, editable=False)

    class Meta:
        indexes = [models.Index(name='activity_score_index', fields=['user', 'timestamp'], include=['change'])]

    def __str__(self):
        return f"{self.change} POINTS FOR {self.user.username} REASON {self.reason}"

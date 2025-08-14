import uuid

from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils.translation import gettext_lazy as _
from .validators import validate_not_future_date, validate_min_age_13

REGION_CHOICES = [
    ('DS', _('Dolnośląskie')),
    ('KP', _('Kujawsko-Pomorskie')),
    ('LB', _('Lubelskie')),
    ('LS', _('Lubuskie')),
    ('LD', _('Łódzkie')),
    ('ML', _('Małopolskie')),
    ('MZ', _('Mazowieckie')),
    ('OP', _('Opolskie')),
    ('PK', _('Podkarpackie')),
    ('PL', _('Podlaskie')),
    ('PM', _('Pomorskie')),
    ('SL', _('Śląskie')),
    ('SK', _('Świętokrzyskie')),
    ('WM', _('Warmińsko-Mazurskie')),
    ('WP', _('Wielkopolskie')),
    ('ZP', _('Zachodniopomorskie')),
    ('NS', _('Nieznany')),  # default region 
]

class UserManager(BaseUserManager):
    def create_user(self, username, email, password, date_of_birth, region='NS', **extra_fields):


        if not email:
            raise ValueError(_('The Email must be set'))
        if not date_of_birth:
            date_of_birth = timezone.now().date()
        
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        email = email.strip().lower()

        user = self.model(
            username=username, 
            email=email,
            date_of_birth=date_of_birth,
            region=region,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password, date_of_birth, region='NS', **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, email, password, date_of_birth, region, **extra_fields)


class User(AbstractUser):

    UUID = models.UUIDField(
        primary_key=   True, 
        default=       uuid.uuid4, 
        editable=      False,
        verbose_name=  _("Unique User ID"),
        help_text=     _("A unique identifier for the user, automatically generated.")
    )

    region         = models.CharField(
        max_length=    2, 
        choices=       REGION_CHOICES,
        verbose_name=  _("Region"),
        help_text=     _("Select the user's region"),
        blank=         False, 
        null=          False,  
    )

    date_of_birth = models.DateField(
        verbose_name=  _("Date of Birth"),
        help_text=     _("Enter the user's date of birth (YYYY-MM-DD)."),   
        validators=[
            validate_not_future_date,       
            validate_min_age_13,   # For now let's assume that the 
            # minimum age is 13 (7-8th year of school)
        ],
        blank=         False,
        null=          False,
    )

    profile_image = models.ImageField(
        upload_to=     'media/profile_images/',
        blank=         True,
        null=          True
    )

    objects = UserManager()

    def __str__(self):
        return f"{self.username} ({self.first_name} {self.last_name})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def activity_score(self):
        return self.activity_scores.aggregate(Sum('change'))['change__sum'] or 0


class LinkedAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, related_name='linked_accounts',
                              on_delete=models.CASCADE)
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

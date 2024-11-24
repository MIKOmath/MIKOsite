import uuid

from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinLengthValidator, MaxLengthValidator


class CustomUserManager(BaseUserManager):
    # Method to create a normal user
    def create_user(self, username, email, password, **extra_fields):
        if not email:
            raise ValueError('The email address is required')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    # Method to create a superuser
    def create_superuser(self, username, email, password, **extra_fields):
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractUser):
    username = models.CharField(max_length=30, unique=True, validators=[MinLengthValidator(5)])
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=128)
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    region = models.CharField(max_length=30, blank=True, validators=[MinLengthValidator(5), MaxLengthValidator(30)])
    date_of_birth = models.DateField(blank=True, null=True)
    problem_counter = models.IntegerField(default=0, blank=True)
    profile_image = models.ImageField(upload_to='media/profile_images/', blank=True, null=True)
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.username} ({self.name} {self.surname})"

    @property
    def full_name(self):
        return f"{self.name} {self.surname}"

    @property
    def activity_score(self):
        return self.activity_scores.aggregate(Sum('change'))['change__sum'] or 0


class LinkedAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, related_name='linked_accounts', on_delete=models.CASCADE)
    external_id = models.CharField(max_length=128, blank=False, null=False)
    platform = models.CharField(max_length=50, blank=False, null=False)
    timestamp = models.DateTimeField(auto_now=True, blank=False, null=False)

    class Meta:
        unique_together = (('external_id', 'platform'), ('user', 'platform'))
        indexes = [
            models.Index(fields=['external_id']),
        ]

    def __str__(self):
        return f"USER {self.user.username} IS {self.external_id} ON {self.platform}"


class ActivityScore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, related_name='activity_scores', on_delete=models.CASCADE)
    change = models.IntegerField(blank=False, null=False)
    reason = models.CharField(max_length=255, blank=False, null=False)
    timestamp = models.DateTimeField(default=timezone.now, blank=False, null=False, editable=False)

    def __str__(self):
        return f"{self.change} POINTS FOR {self.user.username} REASON {self.reason}"

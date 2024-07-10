from django.db import models
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
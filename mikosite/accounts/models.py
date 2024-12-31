import uuid
from django.db import models, IntegrityError
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinLengthValidator, MaxLengthValidator, validate_email, FileExtensionValidator
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

def validate_wojewodztwo(value):
    wojewodztwa = [
        'dolnośląskie',
        'kujawsko-pomorskie',
        'lubelskie',
        'lubuskie',
        'łódzkie',
        'małopolskie',
        'mazowieckie',
        'opolskie',
        'podkarpackie',
        'podlaskie',
        'pomorskie',
        'śląskie',
        'świętokrzyskie',
        'warmińsko-mazurskie',
        'wielkopolskie',
        'zachodniopomorskie'
    ]
    if value.lower() not in wojewodztwa:
        raise ValidationError(
            f'Wybierz poprawne województwo. Dostępne opcje: {", ".join(wojewodztwa)}'
        )


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password, **extra_fields):
        try:
            if not email:
                raise ValueError('Adres e-mail jest wymagany')
            if not username:
                raise ValueError('Nazwa użytkownika jest wymagana')
            if not password:
                raise ValueError('Hasło jest wymagane')

            email = self.normalize_email(email)

            if self.model.objects.filter(username=username).exists():
                raise ValidationError("Ta nazwa użytkownika już jest zajęta.")

            if self.model.objects.filter(email=email).exists():
                logger.info(f"Próba rejestracji przy użyciu istniejącego adresu e-mail: {email}")
                raise ValidationError("Rejestracja się nie powiodła. Sprawdź dane jeszcze raz.")

            user = self.model(
                username=username,
                email=email,
                **extra_fields
            )
            user.set_password(password)

            try:
                user.full_clean(validate_unique=False)
            except ValidationError as e:
                logger.info(f"Walidacja nie powiodła się dla nowego użytkownika: {str(e)}")
                raise ValidationError(str(e))

            try:
                user.save(using=self._db)
                return user
            except IntegrityError as e:
                logger.info(f"Błąd integralności podczas tworzenia użytkownika: {str(e)}")

                raise ValidationError("Nie udało się utworzyć konta")
        except Exception as e:
            if not isinstance(e, (ValueError, ValidationError)):
                logger.error(f"Nieoczekiwany błąd w create_user: {str(e)}")
                raise ValidationError("Wystąpił nieoczekiwany błąd")
            raise

    def create_superuser(self, username, email, password, name="Name", surname="Surname", **extra_fields):

        try:
            extra_fields.setdefault('is_staff', True)
            extra_fields.setdefault('is_superuser', True)

            user = self.create_user(
                username=username,
                email=email,
                password=password,
                name= name,
                surname=surname,
                **extra_fields
            )

            return user

        except Exception as e:
            logger.error(f"Nie udało się utworzyć użytkownika z uprawnieniami administratora: {str(e)}")
            raise

class User(AbstractUser):
    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[MinLengthValidator(5)],
        error_messages={
            'unique': 'Użytkownik o tej nazwie już istnieje.',
            'required': 'To pole nie może być puste.',
        }
    )
    email = models.EmailField(
        max_length=255,
        unique=True,
        validators=[validate_email]
    )
    password = models.CharField(
        max_length=128,
        validators=[MinLengthValidator(8)]
    )
    from django.core.validators import MinLengthValidator

    name = models.CharField(
        max_length=50,
        validators=[MinLengthValidator(3)],  # Enforces a minimum length of 3
        error_messages={
            'blank': 'Pole imię nie może być puste.',
            'max_length': 'Imię nie może przekraczać 50 znaków.',
            'min_length': 'Imię musi mieć co najmniej 3 znaki.',  # Custom error for min length
        }
    )

    surname = models.CharField(
        max_length=50,
        validators=[MinLengthValidator(3)],  # Enforces a minimum length of 3
        error_messages={
            'blank': 'Pole nazwisko nie może być puste.',
            'max_length': 'Nazwisko nie może przekraczać 50 znaków.',
            'min_length': 'Nazwisko musi mieć co najmniej 3 znaki.',  # Custom error for min length
        }
    )

    region = models.CharField(
        max_length=30,
        blank=True,
        validators=[validate_wojewodztwo]
    )
    date_of_birth = models.DateField(auto_now=True, blank=True, null=True)
    profile_image = models.ImageField(
        upload_to='media/profile_images/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['png', 'jpg', 'jpeg'])]
    )
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

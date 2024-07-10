from django.db import models
from django.db import models
from django.conf import settings
from accounts.models import User
# Create your models here.




class Kolo(models.Model):
    date = models.DateField(blank=True, null=True)
    time = models.TimeField(blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    tutors = models.ManyToManyField(User, blank=True)
    theme = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='kolo_images/', blank=True, null=True)
    file = models.FileField(upload_to='kolo_files/', blank=True, null=True)
    level = models.IntegerField(blank=True, null=True)
    finished = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return f"Kolo: {self.theme} on {self.date} at {self.time}"
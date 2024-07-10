from django.db import models
from accounts.models import User

# Create your models here.


class Post(models.Model):
    title = models.CharField(max_length=200, blank=True)
    subtitle = models.CharField(max_length=500, blank=True)
    authors = models.ManyToManyField(User, blank=True)
    file = models.FileField(upload_to='post_files/', blank=True)
    images = models.ManyToManyField('Image', blank=True)
    text_field_1 = models.TextField(max_length=5000, blank=True)
    text_field_2 = models.TextField(max_length=5000, blank=True)
    date = models.DateField(blank=True, null=True)  # Date field
    time = models.TimeField(blank=True, null=True)  # Time field
    def __str__(self):
        
        return f"{self.title}"

class Image(models.Model):
    image = models.ImageField(upload_to='post_images/', blank=True)

    def __str__(self):
        return str(self.image)
# Generated by Django 5.0.6 on 2024-07-06 19:39

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seminars', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='kolo',
            name='date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='kolo',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='kolo',
            name='duration',
            field=models.DurationField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='kolo',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='kolo_files/'),
        ),
        migrations.AlterField(
            model_name='kolo',
            name='finished',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name='kolo',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='kolo_images/'),
        ),
        migrations.AlterField(
            model_name='kolo',
            name='level',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='kolo',
            name='theme',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='kolo',
            name='time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='kolo',
            name='tutors',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
    ]

# Generated by Django 5.1.2 on 2024-11-14 17:10

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainSite', '0002_post_date_post_time'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='authors',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='post',
            name='date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='post',
            name='subtitle',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='time',
            field=models.TimeField(),
        ),
        migrations.AlterField(
            model_name='post',
            name='title',
            field=models.CharField(max_length=200),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['date'], name='mainSite_po_date_dc489a_idx'),
        ),
    ]

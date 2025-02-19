# Generated by Django 5.1.2 on 2024-11-14 17:12

import django.core.validators
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seminars', '0004_seminargroup_rename_level_seminar_difficulty_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='seminar',
            name='date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='seminar',
            name='difficulty',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)]),
        ),
        migrations.AlterField(
            model_name='seminar',
            name='duration',
            field=models.DurationField(),
        ),
        migrations.AlterField(
            model_name='seminar',
            name='featured',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='seminar',
            name='finished',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='seminar',
            name='special_guest',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='seminar',
            name='started',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='seminar',
            name='theme',
            field=models.CharField(max_length=256),
        ),
        migrations.AlterField(
            model_name='seminar',
            name='time',
            field=models.TimeField(),
        ),
        migrations.AlterField(
            model_name='seminargroup',
            name='default_difficulty',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)]),
        ),
        migrations.AddIndex(
            model_name='seminar',
            index=models.Index(fields=['date'], name='seminars_se_date_a108ff_idx'),
        ),
        migrations.AddConstraint(
            model_name='seminar',
            constraint=models.CheckConstraint(condition=models.Q(('started', True), ('finished', False), _connector='OR'), name='if_finished_then_started'),
        ),
    ]

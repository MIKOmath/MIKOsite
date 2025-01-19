# Generated by Django 5.1.3 on 2025-02-20 12:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seminars', '0009_googleformstemplate_seminar_form'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=256)),
                ('date_time', models.DateTimeField()),
                ('pinged', models.BooleanField(default=False)),
                ('seminar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reminder', to='seminars.seminar')),
            ],
        ),
    ]

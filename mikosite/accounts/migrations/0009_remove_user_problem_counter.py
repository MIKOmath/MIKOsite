# Generated by Django 5.1.2 on 2024-11-24 00:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_activityscore_linkedaccount'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='problem_counter',
        ),
    ]

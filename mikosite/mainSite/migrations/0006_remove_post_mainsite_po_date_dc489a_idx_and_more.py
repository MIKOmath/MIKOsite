# Generated by Django 5.1.3 on 2024-12-26 23:58

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainSite', '0005_remove_post_text_field_1_remove_post_text_field_2_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='post',
            name='mainSite_po_date_dc489a_idx',
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['date', 'time'], name='mainSite_po_date_f901e1_idx'),
        ),
    ]

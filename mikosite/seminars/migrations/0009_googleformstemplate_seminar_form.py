# Generated by Django 5.1.3 on 2025-02-20 12:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seminars', '0008_seminar_discord_voice_channel_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='GoogleFormsTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('file', models.FileField(upload_to='google_forms_templates/')),
            ],
        ),
        migrations.AddField(
            model_name='seminar',
            name='form',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='seminars.googleformstemplate'),
        ),
    ]

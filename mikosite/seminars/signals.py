from dataclasses import dataclass

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Seminar, Reminder
from datetime import timedelta, datetime
from django.utils.timezone import make_aware

@receiver(post_save, sender=Seminar)
def create_reminders_for_seminar(sender, instance, created, **kwargs):
    if created:
        reminder_date = make_aware(datetime.combine(instance.date, instance.time) - timedelta(days=1) )
        Reminder.objects.create(seminar=instance,type="invite", date_time=reminder_date)
@receiver(post_save, sender=Seminar)
def update_reminders_on_seminar_change(sender, instance, created, **kwargs):
    if not created:  # Only act if it's an update (not a new instance)
        for reminder in instance.reminder.all():
            reminder.date_time = make_aware(datetime.combine(instance.date,instance.time))
            reminder.save()
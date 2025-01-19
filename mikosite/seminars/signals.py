from datetime import timedelta, datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Seminar, Reminder

hours_before_seminar_to_invite = 1
hours_after_seminar_to_feedback = 0

@receiver(post_save, sender=Seminar)
def create_reminders_for_seminar(sender, instance, created, **kwargs):
    if created:
        reminder_date = datetime.combine(instance.date, instance.time)- timedelta(hours=hours_before_seminar_to_invite)
        Reminder.objects.create(seminar=instance,type="invite", date_time=reminder_date)
        reminder_date = datetime.combine(instance.date, instance.time) + instance.duration + timedelta(hours=hours_after_seminar_to_feedback)
        Reminder.objects.create(seminar=instance, type="feedback", date_time=reminder_date)
    else:
        for reminder in instance.reminder.all():
            if reminder.type == "invite":
                reminder.date_time = datetime.combine(instance.date,instance.time) - timedelta(hours=hours_before_seminar_to_invite)
                reminder.save()
            if reminder.type == "feedback":
                reminder.date_time = datetime.combine(instance.date, instance.time) + instance.duration + timedelta(hours=hours_after_seminar_to_feedback)
                reminder.save()

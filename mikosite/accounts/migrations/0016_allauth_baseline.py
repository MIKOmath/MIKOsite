"""Verification is mandatory from now on, so existing members need verified
EmailAddress rows or their next login would demand confirmation. The 'user'
group granted nothing and was never read; the new signup no longer mints it."""
from django.db import migrations


def forwards(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    EmailAddress = apps.get_model('account', 'EmailAddress')
    Group = apps.get_model('auth', 'Group')

    for user in User.objects.exclude(email='').iterator():
        EmailAddress.objects.get_or_create(
            user_id=user.pk,
            email=user.email.lower(),
            defaults={'verified': True, 'primary': True},
        )

    Group.objects.filter(name='user').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0015_alter_user_date_of_birth_alter_user_email_and_more'),
        ('account', '0009_emailaddress_unique_primary_email'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]

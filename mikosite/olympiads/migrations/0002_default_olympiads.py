from django.db import migrations

# Olympiads MIKO prepares for. Stage names and dates change every school year and are
# filled in through the admin; this only seeds the entries so they are there to configure.
DEFAULT_OLYMPIADS = [
    {'name': 'Olimpiada Matematyczna', 'short_name': 'OM', 'order': 1},
    {'name': 'Olimpiada Informatyczna', 'short_name': 'OI', 'order': 2},
    {'name': 'Olimpiada AI', 'short_name': 'AI', 'order': 3},
]


def create_default_olympiads(apps, schema_editor):
    Olympiad = apps.get_model('olympiads', 'Olympiad')
    for olympiad in DEFAULT_OLYMPIADS:
        Olympiad.objects.get_or_create(name=olympiad['name'], defaults=olympiad)


def remove_default_olympiads(apps, schema_editor):
    Olympiad = apps.get_model('olympiads', 'Olympiad')
    names = [olympiad['name'] for olympiad in DEFAULT_OLYMPIADS]
    Olympiad.objects.filter(name__in=names, stages__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('olympiads', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_olympiads, remove_default_olympiads),
    ]
